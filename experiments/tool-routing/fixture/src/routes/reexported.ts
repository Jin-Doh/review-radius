import { samePrincipalLoose } from "../identity/index.js";

export function revokeSession(actorId: string, targetId: string): boolean {
  return samePrincipalLoose(actorId, targetId);
}
