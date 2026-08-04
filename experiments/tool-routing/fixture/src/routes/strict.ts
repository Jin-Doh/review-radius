import { samePrincipalStrict } from "../identity/principal.js";

export function readOwnProfile(actorId: string, targetId: string): boolean {
  return samePrincipalStrict(actorId, targetId);
}
