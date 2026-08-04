export function sameAccountLoose(left: string, right: string): boolean {
  return left.trim().toLowerCase() === right.trim().toLowerCase();
}
