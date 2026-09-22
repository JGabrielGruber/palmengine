export type StudioEventMap = {
  "canvas:node:added": { nodeId: string };
  "canvas:node:removed": { nodeId: string };
  "canvas:edge:added": { edgeId: string; source: string; target: string };
  "canvas:layout:applied": { mode: string };
  "canvas:group:created": { groupId: string };
  "project:saved": { projectId: string; version: number };
  "project:switched": { projectId: string };
  "simulate:started": { jobId: string };
  "simulate:completed": { jobId: string; status: string };
  "plugin:registered": { id: string; kind: string };
};

type Handler<T> = (payload: T) => void;

const listeners = new Map<string, Set<Handler<unknown>>>();

export const studioEvents = {
  on<K extends keyof StudioEventMap>(
    event: K,
    handler: Handler<StudioEventMap[K]>,
  ): () => void {
    const bucket = listeners.get(event) ?? new Set();
    bucket.add(handler as Handler<unknown>);
    listeners.set(event, bucket);
    return () => bucket.delete(handler as Handler<unknown>);
  },
  emit<K extends keyof StudioEventMap>(event: K, payload: StudioEventMap[K]) {
    const bucket = listeners.get(event);
    if (!bucket) {
      return;
    }
    for (const handler of bucket) {
      handler(payload);
    }
  },
};