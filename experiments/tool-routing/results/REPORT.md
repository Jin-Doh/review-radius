<!-- markdownlint-disable MD013 -->

# Tool-routing benchmark report

## Environment

- Python: `3.14.6`
- ast-grep: `ast-grep 0.45.0`
- TypeScript language server: `5.3.0`
- Graphify: `graphifyy==0.9.32 via uvx`

## Results

| Method | Recall | Precision | Token proxy | Query ms | Cold index ms | Missed |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| rg+raw | 75.00% | 75.00% | 1883 | 16.63 | - | readAuditLog, transferAccount |
| rg+ast | 87.50% | 87.50% | 2171 | 33.90 | - | readAuditLog |
| rg+ast+lsp | 100.00% | 100.00% | 2374 | 558.21 | - | - |
| graphify-query | 87.50% | 100.00% | 589 | 146.31 | 461.69 | rotateCredential |
| graphify+ast+lsp | 100.00% | 100.00% | 2663 | 704.52 | 461.69 | - |
| routed-compact | 100.00% | 100.00% | 451 | 704.52 | 461.69 | - |

`Token proxy = ceil((tool output bytes + modeled source-read bytes) / 4)`.
It is intended for relative comparison within this fixture only.

## Candidate details

### rg+raw

- Candidates: `deletePrincipal, ownsResource, revokeSession, rotateCredential, sameAccountLoose, samePrincipalLoose, samePrincipalStrict, searchDirectory`
- False positives: `samePrincipalStrict, searchDirectory`
- Missed: `readAuditLog, transferAccount`
- Tool bytes: `6151`
- Modeled source bytes: `1380`

### rg+ast

- Candidates: `deletePrincipal, ownsResource, revokeSession, rotateCredential, sameAccountLoose, samePrincipalLoose, samePrincipalStrict, transferAccount`
- False positives: `samePrincipalStrict`
- Missed: `readAuditLog`
- Tool bytes: `7291`
- Modeled source bytes: `1393`

### rg+ast+lsp

- Candidates: `deletePrincipal, ownsResource, readAuditLog, revokeSession, rotateCredential, sameAccountLoose, samePrincipalLoose, transferAccount`
- False positives: `-`
- Missed: `-`
- Tool bytes: `8031`
- Modeled source bytes: `1464`

### graphify-query

- Candidates: `deletePrincipal, ownsResource, readAuditLog, revokeSession, sameAccountLoose, samePrincipalLoose, transferAccount`
- False positives: `-`
- Missed: `rotateCredential`
- Tool bytes: `1154`
- Modeled source bytes: `1200`

### graphify+ast+lsp

- Candidates: `deletePrincipal, ownsResource, readAuditLog, revokeSession, rotateCredential, sameAccountLoose, samePrincipalLoose, transferAccount`
- False positives: `-`
- Missed: `-`
- Tool bytes: `9185`
- Modeled source bytes: `1464`

### routed-compact

- Candidates: `deletePrincipal, ownsResource, readAuditLog, revokeSession, rotateCredential, sameAccountLoose, samePrincipalLoose, transferAccount`
- False positives: `-`
- Missed: `-`
- Tool bytes: `393`
- Modeled source bytes: `1411`

## Observations

- Text search reached 75.00% recall and included safe decoys.
- AST plus LSP reached full recall and precision, including the transitive wrapper caller.
- Graphify alone used 68.72% fewer proxy tokens than text search, but missed the aliased call `rotateCredential`.
- Naively accumulating every raw tool output increased the proxy token count.
- Compact routing retained full recall and precision with 76.05% fewer proxy tokens than text search.

The fixture is intentionally small and synthetic. These findings validate the routing mechanism, not repository-scale savings; a larger real-repository trial is still required.
