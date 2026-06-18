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

export type CanvasNode = {
  id: string;
  kind: PaletteNodeKind;
  label: string;
  x: number;
  y: number;
  ref?: string;
  meta?: Record<string, unknown>;
};

export type CanvasEdge = {
  id: string;
  source: string;
  target: string;
};

export type StudioCanvas = {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
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