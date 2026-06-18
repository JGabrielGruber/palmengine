import { bootstrap } from "../bootstrap";
import type {
  FlowDefinitionJson,
  FlowSummary,
  PaletteResponse,
  ProcessDefinitionJson,
  ProcessSummary,
  StudioDraft,
  StudioTemplateDetail,
  StudioTemplateSummary,
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
      headers: options.body
        ? { "Content-Type": "application/json", Accept: "application/json" }
        : { Accept: "application/json" },
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const message =
        (payload as { message?: string }).message ??
        `API ${response.status}: ${path}`;
      throw new Error(message);
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

  listProcesses() {
    return this.fetch<{ processes: ProcessSummary[] }>("/processes?limit=200");
  }

  getProcess(processId: string) {
    return this.fetch<ProcessDefinitionJson>(
      `/processes/${encodeURIComponent(processId)}`,
    );
  }

  saveFlow(flow: FlowDefinitionJson) {
    return this.fetch<{ saved: boolean; flow: FlowDefinitionJson }>(
      "/studio/definitions/flows",
      { method: "POST", body: flow },
    );
  }

  saveProcess(process: ProcessDefinitionJson) {
    return this.fetch<{ saved: boolean; process: ProcessDefinitionJson }>(
      "/studio/definitions/processes",
      { method: "POST", body: process },
    );
  }

  listTemplates() {
    return this.fetch<{
      templates: StudioTemplateSummary[];
      categories: string[];
    }>("/studio/templates");
  }

  getTemplate(templateId: string) {
    return this.fetch<{ template: StudioTemplateDetail }>(
      `/studio/templates/${encodeURIComponent(templateId)}`,
    );
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