import { sameAccountLoose } from "../identity/account.js";

export function transferAccount(actorId: string, accountId: string): boolean {
  return sameAccountLoose(actorId, accountId);
}
