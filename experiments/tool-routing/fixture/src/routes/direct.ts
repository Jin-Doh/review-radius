import { samePrincipalLoose } from "../identity/principal.js";

export function deletePrincipal(actorId: string, targetId: string): boolean {
  return samePrincipalLoose(actorId, targetId);
}
