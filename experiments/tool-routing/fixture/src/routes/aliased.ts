import { samePrincipalLoose as principalMatches } from "../identity/principal.js";

export function rotateCredential(actorId: string, targetId: string): boolean {
  return principalMatches(actorId, targetId);
}
