import { startSession } from "./actions";

// One quiz session per browser tab: refreshes and page changes reuse it,
// reopening the site in a new tab starts a new one.
const KEY = "phishingSessionId";

// Shared so double-mounts or fast clicks don't create two sessions
let pending: Promise<number> | null = null;

export function getSessionId(): Promise<number> {
  const saved = sessionStorage.getItem(KEY);
  if (saved !== null) return Promise.resolve(Number(saved));

  pending ??= startSession()
    .then((id) => {
      sessionStorage.setItem(KEY, String(id));
      return id;
    })
    .finally(() => {
      pending = null;
    });
  return pending;
}
