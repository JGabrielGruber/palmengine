export type StudioBootstrap = {
  version: string;
  runtime: string;
  apiBase: string;
  explorer: string;
  studio: string;
};

export type PaletteNodeKind =
  | "action"
  | "condition"
  | "resource"
  | "transform"
  | "pattern"
  | "flow";

export type PaletteItem = {
  id: string;
  kind: PaletteNodeKind;
  label: string;
  description: string;
  draggable: boolean;
  ref?: string;
  definition_id?: string;
  provider?: string;
  action?: string;
  param_keys?: string[];
  mode?: string;
  pattern?: string;
  class?: string;
};

export type PaletteSection = {
  id: string;
  label: string;
  items: PaletteItem[];
};

export type PaletteResponse = {
  version: string;
  sections: PaletteSection[];
};

export type CanvasGroupKind = "parallel" | "subflow";

export type CanvasGroup = {
  id: string;
  label: string;
  kind: CanvasGroupKind;
  x: number;
  y: number;
  width: number;
  height: number;
};

export type CanvasNode = {
  id: string;
  kind: PaletteNodeKind;
  label: string;
  x: number;
  y: number;
  ref?: string;
  parentId?: string;
  meta?: Record<string, unknown>;
};

export type CanvasEdge = {
  id: string;
  source: string;
  target: string;
  label?: string;
};

export type FlowSummary = {
  flow_id: string;
  name: string;
  pattern: string;
  has_state_schema: boolean;
};

export type ProcessSummary = {
  process_id: string;
  name: string;
  storage: string;
  flow_count: number;
};

export type StudioTemplateSummary = {
  id: string;
  name: string;
  description: string;
  pattern: string;
  category: string;
  tags: string[];
};

export type StudioTemplateDetail = StudioTemplateSummary & {
  flow: FlowDefinitionJson;
};

export type StudioCanvas = {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  groups?: CanvasGroup[];
};

export type StudioProject = {
  id: string;
  name: string;
  pattern: string;
  canvas: StudioCanvas;
  draftVersion: number;
  updatedAt: string;
  createdAt: string;
};

export type JobContext = {
  found?: boolean;
  job_id: string;
  status: string;
  pattern?: {
    pattern?: string;
    step?: string;
    prompt?: string;
    field_type?: string;
    choices?: string[];
    validation_error?: string;
    answers?: Record<string, unknown>;
  };
  wizard_progress?: Record<string, unknown>;
  next_actions?: Array<{ action: string; description: string }>;
  error?: string;
  result?: unknown;
};

export type StudioDraft = {
  id: string;
  name: string;
  pattern: string;
  canvas: StudioCanvas;
  updatedAt: string;
  createdAt?: string;
};

export type FlowDefinitionJson = {
  version: number;
  kind: "flow";
  name: string;
  pattern: string;
  options: Record<string, unknown>;
  id?: string;
};

export type ProcessDefinitionJson = {
  version: number;
  kind: "process";
  name: string;
  storage: string;
  metadata: Record<string, unknown>;
  flows: FlowDefinitionJson[];
  id?: string;
};