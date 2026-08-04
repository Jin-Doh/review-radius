import { samePrincipalLoose } from "../identity/principal.js";

export function ownsResource(actorId: string, ownerId: string): boolean {
  return samePrincipalLoose(actorId, ownerId);
}
