export function samePrincipalLoose(left: string, right: string): boolean {
  return left.toLowerCase() === right.toLowerCase();
}

export function samePrincipalStrict(left: string, right: string): boolean {
  return left === right;
}
