export function searchDirectory(entries: string[], query: string): string[] {
  return entries.filter((entry) =>
    entry.toLowerCase().includes(query.toLowerCase()),
  );
}
