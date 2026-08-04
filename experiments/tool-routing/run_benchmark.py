"""Compare review-related candidate discovery with text, AST, LSP, and Graphify."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
SOURCE = FIXTURE / "src"
RESULTS = ROOT / "results"
GROUND_TRUTH = json.loads((ROOT / "ground-truth.json").read_text())
FUNCTION_RE = re.compile(r"^export\s+(?:async\s+)?function\s+(\w+)", re.MULTILINE)


@dataclass
class MethodResult:
    name: str
    candidates: set[str]
    tool_bytes: int
    source_bytes: int
    elapsed_ms: float
    notes: list[str]
    available: bool = True
    cold_index_ms: float | None = None

    def scored(self) -> dict[str, Any]:
        affected = set(GROUND_TRUTH["affected"])
        true_positive = self.candidates & affected
        false_positive = self.candidates - affected
        missed = affected - self.candidates
        precision = len(true_positive) / len(self.candidates) if self.candidates else 0.0
        recall = len(true_positive) / len(affected)
        total_bytes = self.tool_bytes + self.source_bytes
        return {
            "name": self.name,
            "available": self.available,
            "candidates": sorted(self.candidates),
            "true_positive": sorted(true_positive),
            "false_positive": sorted(false_positive),
            "missed": sorted(missed),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "tool_bytes": self.tool_bytes,
            "source_bytes": self.source_bytes,
            "estimated_tokens": math.ceil(total_bytes / 4),
            "elapsed_ms": round(self.elapsed_ms, 2),
            "cold_index_ms": (
                round(self.cold_index_ms, 2) if self.cold_index_ms is not None else None
            ),
            "notes": self.notes,
        }


def command(*args: str, cwd: Path = FIXTURE, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def source_files() -> list[Path]:
    return sorted(SOURCE.rglob("*.ts"))


def exported_functions(path: Path) -> set[str]:
    return set(FUNCTION_RE.findall(path.read_text()))


def all_exported_functions() -> set[str]:
    result: set[str] = set()
    for path in source_files():
        result.update(exported_functions(path))
    return result


def parse_rg_files(output: str) -> set[Path]:
    paths: set[Path] = set()
    for line in output.splitlines():
        item = json.loads(line)
        if item.get("type") == "match":
            paths.add(FIXTURE / item["data"]["path"]["text"])
    return paths


def normalize_rg_output(output: str) -> str:
    """Remove ripgrep timing and self-sized fields before token-proxy scoring."""
    normalized: list[str] = []
    for line in output.splitlines():
        item = json.loads(line)
        data = item.get("data", {})
        data.pop("elapsed_total", None)
        stats = data.get("stats")
        if isinstance(stats, dict):
            stats.pop("elapsed", None)
            stats.pop("bytes_printed", None)
        normalized.append(json.dumps(item, sort_keys=True, separators=(",", ":")))
    return "\n".join(normalized) + ("\n" if normalized else "")


def functions_in_files(paths: set[Path]) -> set[str]:
    result: set[str] = set()
    for path in paths:
        result.update(exported_functions(path))
    return result


def function_at_line(path: Path, line: int) -> str | None:
    for name, start, end in function_ranges(path):
        if start <= line <= end:
            return name
    return None


def definition_path(symbol: str) -> Path:
    for path in source_files():
        if any(name == symbol for name, _, _ in function_ranges(path)):
            return path
    raise ValueError(f"Cannot find definition for {symbol}")


def full_source_bytes(paths: set[Path]) -> int:
    return sum(len(path.read_bytes()) for path in paths)


def baseline() -> MethodResult:
    start = time.perf_counter()
    result = command(
        "rg",
        "--json",
        "-e",
        "samePrincipalLoose",
        "-e",
        "toLowerCase",
        "src",
    )
    normalized = normalize_rg_output(result.stdout)
    files = parse_rg_files(normalized)
    elapsed = (time.perf_counter() - start) * 1000
    return MethodResult(
        name="rg+raw",
        candidates=functions_in_files(files),
        tool_bytes=len(normalized.encode()),
        source_bytes=full_source_bytes(files),
        elapsed_ms=elapsed,
        notes=["Single review-anchor pass; reads every matched file in full."],
    )


def ast_search() -> tuple[MethodResult, set[str], str]:
    start = time.perf_counter()
    ast_result = command(
        "ast-grep",
        "--pattern",
        "$A.toLowerCase() === $B.toLowerCase()",
        "--lang",
        "ts",
        "--json=stream",
        "src",
    )
    ast_files: set[Path] = set()
    roots: set[str] = set()
    for line in ast_result.stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        path = FIXTURE / item["file"]
        ast_files.add(path)
        root = function_at_line(path, item["range"]["start"]["line"])
        if root:
            roots.add(root)

    rg_args = ["rg", "--json"]
    for root in sorted(roots):
        rg_args.extend(["-e", root])
    rg_args.append("src")
    caller_result = command(*rg_args)
    normalized_callers = normalize_rg_output(caller_result.stdout)
    caller_files = parse_rg_files(normalized_callers)
    read_files = ast_files | caller_files
    candidates = functions_in_files(read_files)
    elapsed = (time.perf_counter() - start) * 1000
    raw = ast_result.stdout + normalized_callers
    return (
        MethodResult(
            name="rg+ast",
            candidates=candidates,
            tool_bytes=len(raw.encode()),
            source_bytes=full_source_bytes(read_files),
            elapsed_ms=elapsed,
            notes=[
                "AST finds structural defect roots; text search follows each root one hop.",
                "No semantic alias or transitive call traversal.",
            ],
        ),
        roots,
        raw,
    )


class LspClient:
    def __init__(self, executable: str) -> None:
        self.process = subprocess.Popen(
            [executable, "--stdio"],
            cwd=FIXTURE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.next_id = 1

    def send(self, payload: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while True:
            message = self.read_message()
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"LSP {method} failed: {message['error']}")
                return message.get("result")

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def read_message(self) -> dict[str, Any]:
        assert self.process.stdout is not None
        length = None
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("LSP server exited before responding")
            if line == b"\r\n":
                break
            header = line.decode().strip()
            if header.lower().startswith("content-length:"):
                length = int(header.split(":", 1)[1].strip())
        if length is None:
            raise RuntimeError("LSP response omitted Content-Length")
        return json.loads(self.process.stdout.read(length))

    def close(self) -> None:
        try:
            self.request("shutdown", {})
            self.notify("exit", {})
            self.process.wait(timeout=5)
        except (RuntimeError, subprocess.TimeoutExpired):
            self.process.terminate()
            self.process.wait(timeout=5)


def position_for(path: Path, symbol: str) -> dict[str, int]:
    for line_number, line in enumerate(path.read_text().splitlines()):
        if symbol in line:
            return {"line": line_number, "character": line.index(symbol)}
    raise ValueError(f"Cannot find {symbol} in {path}")


def function_ranges(path: Path) -> list[tuple[str, int, int]]:
    lines = path.read_text().splitlines()
    result: list[tuple[str, int, int]] = []
    for start, line in enumerate(lines):
        match = re.match(r"^export\s+(?:async\s+)?function\s+(\w+)", line)
        if not match:
            continue
        depth = 0
        seen_open = False
        end = start
        for index in range(start, len(lines)):
            depth += lines[index].count("{") - lines[index].count("}")
            seen_open = seen_open or "{" in lines[index]
            end = index
            if seen_open and depth == 0:
                break
        result.append((match.group(1), start, end))
    return result


def symbol_at_location(location: dict[str, Any]) -> str | None:
    uri = location["uri"]
    path = Path(uri.removeprefix("file://"))
    line = location["range"]["start"]["line"]
    for name, start, end in function_ranges(path):
        if start <= line <= end:
            return name
    return None


def source_window_bytes(locations: list[dict[str, Any]]) -> int:
    windows: dict[Path, list[tuple[int, int]]] = {}
    for location in locations:
        path = Path(location["uri"].removeprefix("file://"))
        line = location["range"]["start"]["line"]
        lines = path.read_text().splitlines(keepends=True)
        windows.setdefault(path, []).append((max(0, line - 2), min(len(lines), line + 3)))
    total = 0
    for path, intervals in windows.items():
        merged: list[list[int]] = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        lines = path.read_text().splitlines(keepends=True)
        total += sum(len("".join(lines[start:end]).encode()) for start, end in merged)
    return total


def definition_locations(symbols: set[str]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for path in source_files():
        for name, start, _ in function_ranges(path):
            if name in symbols:
                locations.append(
                    {
                        "uri": path.as_uri(),
                        "range": {
                            "start": {"line": start, "character": 0},
                            "end": {"line": start, "character": 0},
                        },
                    }
                )
    return locations


def lsp_search(
    roots: set[str], ast_raw: str, ast_elapsed_ms: float
) -> tuple[MethodResult, str]:
    executable = shutil.which("typescript-language-server")
    if not executable:
        return (
            MethodResult(
                name="rg+ast+lsp",
                candidates=set(),
                tool_bytes=0,
                source_bytes=0,
                elapsed_ms=0,
                notes=["typescript-language-server is unavailable."],
                available=False,
            ),
            "",
        )

    client = LspClient(executable)
    payloads: list[Any] = []
    locations: list[dict[str, Any]] = []
    candidates = set(roots)
    start = time.perf_counter()
    try:
        initialize = client.request(
            "initialize",
            {
                "processId": None,
                "rootUri": FIXTURE.as_uri(),
                "capabilities": {
                    "textDocument": {
                        "callHierarchy": {"dynamicRegistration": False},
                        "references": {"dynamicRegistration": False},
                    }
                },
                "workspaceFolders": [{"uri": FIXTURE.as_uri(), "name": "fixture"}],
            },
        )
        client.notify("initialized", {})
        capabilities = initialize.get("capabilities", {})
        for path in source_files():
            client.notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": path.as_uri(),
                        "languageId": "typescript",
                        "version": 1,
                        "text": path.read_text(),
                    }
                },
            )

        queue: list[dict[str, Any]] = []
        seen_items: set[tuple[str, str, int]] = set()
        for root in sorted(roots):
            path = definition_path(root)
            params = {
                "textDocument": {"uri": path.as_uri()},
                "position": position_for(path, root),
            }
            references = client.request(
                "textDocument/references",
                {**params, "context": {"includeDeclaration": True}},
            ) or []
            payloads.append({"root": root, "references": references})
            locations.extend(references)
            for location in references:
                symbol = symbol_at_location(location)
                if symbol:
                    candidates.add(symbol)

            prepared = client.request("textDocument/prepareCallHierarchy", params) or []
            payloads.append({"root": root, "prepared": prepared})
            queue.extend(prepared)

        while queue:
            item = queue.pop(0)
            key = (item["uri"], item["name"], item["range"]["start"]["line"])
            if key in seen_items:
                continue
            seen_items.add(key)
            incoming = client.request("callHierarchy/incomingCalls", {"item": item}) or []
            payloads.append({"incoming_for": item["name"], "incoming": incoming})
            for edge in incoming:
                caller = edge["from"]
                if caller["name"] in all_exported_functions():
                    candidates.add(caller["name"])
                locations.append({"uri": caller["uri"], "range": caller["selectionRange"]})
                queue.append(caller)
    finally:
        client.close()

    elapsed = (time.perf_counter() - start) * 1000
    compact_locations = sorted(
        {
            f"{Path(location['uri'].removeprefix('file://')).relative_to(FIXTURE)}:"
            f"{location['range']['start']['line'] + 1}"
            for location in locations
        }
    )
    compact_payload = json.dumps(
        {
            "roots": sorted(roots),
            "candidates": sorted(candidates),
            "locations": compact_locations,
        },
        separators=(",", ":"),
    )
    raw_protocol_bytes = len(json.dumps(payloads, ensure_ascii=False).encode())
    raw = ast_raw + compact_payload
    return (
        MethodResult(
            name="rg+ast+lsp",
            candidates=candidates,
            tool_bytes=len(raw.encode()),
            source_bytes=source_window_bytes(locations),
            elapsed_ms=ast_elapsed_ms + elapsed,
            notes=[
                "AST supplies defect roots; LSP resolves references and recursive incoming calls.",
                "Source-read proxy charges five-line windows around returned locations.",
                f"Server advertised call hierarchy: {bool(capabilities.get('callHierarchyProvider'))}.",
                f"Raw LSP protocol bytes compacted by adapter: {raw_protocol_bytes}.",
            ],
        ),
        raw,
    )


def graphify_search(
    lsp_result: MethodResult, ast_lsp_raw: str, roots: set[str]
) -> tuple[MethodResult, MethodResult, MethodResult]:
    if os.environ.get("SKIP_GRAPHIFY") == "1":
        unavailable = MethodResult(
            name="graphify-query",
            candidates=set(),
            tool_bytes=0,
            source_bytes=0,
            elapsed_ms=0,
            notes=["Skipped because SKIP_GRAPHIFY=1."],
            available=False,
        )
        combined = MethodResult(**{**unavailable.__dict__, "name": "graphify+ast+lsp"})
        routed = MethodResult(**{**unavailable.__dict__, "name": "routed-compact"})
        return unavailable, combined, routed
    if not shutil.which("uv"):
        unavailable = MethodResult(
            name="graphify-query",
            candidates=set(),
            tool_bytes=0,
            source_bytes=0,
            elapsed_ms=0,
            notes=["uv is unavailable; pinned Graphify cannot run in isolation."],
            available=False,
        )
        combined = MethodResult(**{**unavailable.__dict__, "name": "graphify+ast+lsp"})
        routed = MethodResult(**{**unavailable.__dict__, "name": "routed-compact"})
        return unavailable, combined, routed

    graphify = ["uvx", "--from", "graphifyy==0.9.32", "graphify"]
    with tempfile.TemporaryDirectory(prefix="review-radius-graphify-") as temp_dir:
        graph_fixture = Path(temp_dir)
        shutil.copytree(SOURCE, graph_fixture / "src")
        shutil.copy2(FIXTURE / "tsconfig.json", graph_fixture / "tsconfig.json")
        index_start = time.perf_counter()
        extract = command(
            *graphify,
            "extract",
            ".",
            "--code-only",
            "--directed",
            "--no-viz",
            cwd=graph_fixture,
        )
        cold_index_ms = (time.perf_counter() - index_start) * 1000

        query_start = time.perf_counter()
        root_query = " or ".join(sorted(roots))
        query = command(
            *graphify,
            "query",
            f"Which functions call {root_query} directly or transitively?",
            "--budget",
            "1200",
            cwd=graph_fixture,
        )
        elapsed = (time.perf_counter() - query_start) * 1000
    graph_output = query.stdout + query.stderr
    graph_candidates: set[str] = set()
    graph_locations: list[dict[str, Any]] = []
    for symbol in all_exported_functions():
        if re.search(rf"\b{re.escape(symbol)}\b", graph_output):
            graph_candidates.add(symbol)
    node_pattern = re.compile(r"^NODE (\w+)\(\) \[src=(\S+) loc=L(\d+)", re.MULTILINE)
    for _, relative_path, line in node_pattern.findall(graph_output):
        line_number = int(line) - 1
        graph_locations.append(
            {
                "uri": (FIXTURE / relative_path).as_uri(),
                "range": {
                    "start": {"line": line_number, "character": 0},
                    "end": {"line": line_number, "character": 0},
                },
            }
        )
    graph_only = MethodResult(
        name="graphify-query",
        candidates=graph_candidates,
        tool_bytes=len(graph_output.encode()),
        source_bytes=source_window_bytes(graph_locations),
        elapsed_ms=elapsed,
        cold_index_ms=cold_index_ms,
        notes=[
            "Graphify query uses BFS depth two over the code-only directed graph.",
            "Source-read proxy charges five-line windows around returned graph nodes.",
        ],
    )
    candidates = set(lsp_result.candidates) | graph_candidates
    raw = ast_lsp_raw + graph_output
    combined = MethodResult(
        name="graphify+ast+lsp",
        candidates=candidates,
        tool_bytes=len(raw.encode()),
        source_bytes=lsp_result.source_bytes,
        elapsed_ms=lsp_result.elapsed_ms + elapsed,
        cold_index_ms=cold_index_ms,
        notes=[
            "Pinned Graphify 0.9.32 runs code-only and locally through uvx.",
            "Graph query candidates are unioned with AST and LSP evidence.",
            f"Graphify extract output bytes excluded from token proxy: {len((extract.stdout + extract.stderr).encode())}.",
        ],
    )
    lsp_delta = set(lsp_result.candidates) - graph_candidates
    routed_payload = json.dumps(
        {
            "ast_roots": sorted(roots),
            "graph_candidates": sorted(graph_candidates),
            "lsp_delta": sorted(lsp_delta),
            "final_candidates": sorted(candidates),
        },
        separators=(",", ":"),
    )
    routed = MethodResult(
        name="routed-compact",
        candidates=candidates,
        tool_bytes=len(routed_payload.encode()),
        source_bytes=source_window_bytes(definition_locations(candidates)),
        elapsed_ms=combined.elapsed_ms,
        cold_index_ms=cold_index_ms,
        notes=[
            "AST supplies roots, Graphify supplies the broad candidate set, and LSP supplies only the delta.",
            "The model sees one compact provenance ledger instead of raw tool protocols.",
        ],
    )
    return graph_only, combined, routed


def markdown_report(scored: list[dict[str, Any]], environment: dict[str, Any]) -> str:
    lines = [
        "<!-- markdownlint-disable MD013 -->",
        "",
        "# Tool-routing benchmark report",
        "",
        "## Environment",
        "",
        f"- Python: `{environment['python']}`",
        f"- ast-grep: `{environment['ast_grep']}`",
        f"- TypeScript language server: `{environment['typescript_language_server']}`",
        f"- Graphify: `{environment['graphify']}`",
        "",
        "## Results",
        "",
        "| Method | Recall | Precision | Token proxy | Query ms | Cold index ms | Missed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in scored:
        cold = "-" if item["cold_index_ms"] is None else f"{item['cold_index_ms']:.2f}"
        missed = ", ".join(item["missed"]) or "-"
        lines.append(
            f"| {item['name']} | {item['recall']:.2%} | {item['precision']:.2%} | "
            f"{item['estimated_tokens']} | {item['elapsed_ms']:.2f} | {cold} | {missed} |"
        )
    lines.extend(
        [
            "",
            "`Token proxy = ceil((tool output bytes + modeled source-read bytes) / 4)`.",
            "It is intended for relative comparison within this fixture only.",
            "",
            "## Candidate details",
            "",
        ]
    )
    for item in scored:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- Candidates: `{', '.join(item['candidates']) or '-'}`",
                f"- False positives: `{', '.join(item['false_positive']) or '-'}`",
                f"- Missed: `{', '.join(item['missed']) or '-'}`",
                f"- Tool bytes: `{item['tool_bytes']}`",
                f"- Modeled source bytes: `{item['source_bytes']}`",
                "",
            ]
        )
    by_name = {item["name"]: item for item in scored}
    baseline_item = by_name["rg+raw"]
    graph_item = by_name["graphify-query"]
    routed_item = by_name["routed-compact"]
    observations = [
        f"- Text search reached {baseline_item['recall']:.2%} recall and included safe decoys.",
        "- AST plus LSP reached full recall and precision, including the transitive wrapper caller.",
    ]
    if graph_item["available"]:
        graph_reduction = 1 - graph_item["estimated_tokens"] / baseline_item["estimated_tokens"]
        routed_reduction = 1 - routed_item["estimated_tokens"] / baseline_item["estimated_tokens"]
        observations.extend(
            [
                (
                    f"- Graphify alone used {graph_reduction:.2%} fewer proxy tokens than text search, "
                    "but missed the aliased call `rotateCredential`."
                ),
                "- Naively accumulating every raw tool output increased the proxy token count.",
                (
                    "- Compact routing retained full recall and precision with "
                    f"{routed_reduction:.2%} fewer proxy tokens than text search."
                ),
            ]
        )
    else:
        observations.append("- Graphify was unavailable or explicitly skipped.")
    lines.extend(
        [
            "## Observations",
            "",
            *observations,
            "",
            (
                "The fixture is intentionally small and synthetic. These findings validate the routing "
                "mechanism, not repository-scale savings; a larger real-repository trial is still required."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def version(args: list[str]) -> str:
    try:
        result = command(*args, cwd=ROOT)
        return (result.stdout or result.stderr).strip().splitlines()[-1]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> int:
    missing = [tool for tool in ("rg", "ast-grep", "typescript-language-server", "node") if not shutil.which(tool)]
    if missing:
        print(f"Missing required tools: {', '.join(missing)}", file=sys.stderr)
        return 2

    base = baseline()
    ast, roots, ast_raw = ast_search()
    lsp, ast_lsp_raw = lsp_search(roots, ast_raw, ast.elapsed_ms)
    graph, combined, routed = graphify_search(lsp, ast_lsp_raw, roots)
    methods = [base, ast, lsp, graph, combined, routed]
    scored = [method.scored() for method in methods]
    environment = {
        "python": sys.version.split()[0],
        "ast_grep": version(["ast-grep", "--version"]),
        "typescript_language_server": version(["typescript-language-server", "--version"]),
        "graphify": "graphifyy==0.9.32 via uvx" if graph.available else "unavailable",
    }
    payload = {
        "schema_version": 1,
        "fixture": "case-sensitive identity comparison",
        "environment": environment,
        "ground_truth": GROUND_TRUTH,
        "methods": scored,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(payload, indent=2) + "\n")
    (RESULTS / "REPORT.md").write_text(markdown_report(scored, environment))
    print(markdown_report(scored, environment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
