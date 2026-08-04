import { ownsResource } from "../policies/ownership.js";

export function readAuditLog(actorId: string, ownerId: string): boolean {
  return ownsResource(actorId, ownerId);
}
