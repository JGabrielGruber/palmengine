import { bootstrap } from "../bootstrap";
import type {
  FlowDefinitionJson,
  FlowSummary,
  PaletteResponse,
  StudioDraft,
} from "../types";

type RequestOptions = {
  method?: string;
  body?: unknown;
};

export class StudioApiClient {
  constructor(private readonly baseUrl: string = bootstrap.apiBase) {}

  async fetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: options.method ?? "GET",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API ${response.status}: ${path}`);
    }
    return (await response.json()) as T;
  }

  palette() {
    return this.fetch<PaletteResponse>("/studio/palette");
  }

  listFlows() {
    return this.fetch<{ flows: FlowSummary[] }>("/flows?limit=200");
  }

  getFlow(flowId: string) {
    return this.fetch<FlowDefinitionJson>(`/flows/${encodeURIComponent(flowId)}`);
  }

  listDrafts() {
    return this.fetch<{ drafts: Array<{ id: string; name: string; updated_at: string }> }>(
      "/studio/drafts",
    );
  }

  getDraft(id: string) {
    return this.fetch<{ draft: Record<string, unknown> }>(`/studio/drafts/${id}`);
  }

  saveDraft(payload: {
    id?: string;
    name: string;
    pattern: string;
    canvas: StudioDraft["canvas"];
    created_at?: string;
  }) {
    return this.fetch<{ draft: Record<string, unknown> }>("/studio/drafts", {
      method: "POST",
      body: payload,
    });
  }
}

export const api = new StudioApiClient();