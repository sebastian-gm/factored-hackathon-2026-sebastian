// No customer data or credentials are stored here. Every request belongs to one
// generation; retired responses are discarded even if the server finished them.
let generation = 0;
let blocked = false;
let authenticated = false;
const requests = new Set<AbortController>();
export const SESSION_EVENT = "aclara:session-invalid";
const channelName = "aclara-profile-generation";
const notificationKey = "aclara.profile-generation";
const source = crypto.randomUUID();
export type ProfileNotice = "changing" | "settled";

export function retireWorkspace(stop = true) {
  generation++;
  blocked = stop;
  for (const request of requests) request.abort();
  requests.clear();
  return generation;
}
export function configureWorkspace(
  enabled: boolean,
  stop: boolean,
  hasSession = enabled,
) {
  authenticated = hasSession;
  blocked = stop;
}
export function workspaceRequest(path: string, signal?: AbortSignal) {
  const metadata =
    path === "me" || path === "config" || path.startsWith("auth/");
  if (blocked && !metadata)
    throw new DOMException("Workspace changing", "AbortError");
  const epoch = generation;
  const controller = new AbortController();
  requests.add(controller);
  const abort = () => controller.abort();
  signal?.addEventListener("abort", abort, { once: true });
  if (signal?.aborted) controller.abort();
  return {
    signal: controller.signal,
    current: () => epoch === generation && !controller.signal.aborted,
    release: () => {
      requests.delete(controller);
      signal?.removeEventListener("abort", abort);
    },
  };
}
export function invalidateSession() {
  if (!authenticated) return;
  authenticated = false;
  retireWorkspace();
  window.dispatchEvent(new Event(SESSION_EVENT));
}
export function notifyProfileChange(kind: ProfileNotice) {
  // A random notification only: no profile, customer, token or session ID.
  const notice = { kind, nonce: crypto.randomUUID(), source };
  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel(channelName);
    channel.postMessage(notice);
    channel.close();
  } else {
    localStorage.setItem(notificationKey, JSON.stringify(notice));
  }
}
export function listenProfileChanges(receive: (kind: ProfileNotice) => void) {
  const accept = (value: unknown) => {
    if (
      value &&
      typeof value === "object" &&
      "kind" in value &&
      "source" in value &&
      value.source !== source &&
      (value.kind === "changing" || value.kind === "settled")
    )
      receive(value.kind);
  };
  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel(channelName);
    channel.onmessage = (event: MessageEvent<unknown>) => accept(event.data);
    return () => channel.close();
  }
  const storage = (event: StorageEvent) => {
    if (event.key !== notificationKey || !event.newValue) return;
    try {
      accept(JSON.parse(event.newValue));
    } catch {
      /* Ignore invalid notices. */
    }
  };
  window.addEventListener("storage", storage);
  return () => window.removeEventListener("storage", storage);
}
