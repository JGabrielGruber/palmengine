export type StudioBootstrap = {
  version: string;
  runtime: string;
  apiBase: string;
  explorer: string;
  studio: string;
};

export type PaletteNodeKind = "action" | "condition" | "resource" | "transform";

export type PaletteNode = {
  id: string;
  kind: PaletteNodeKind;
  label: string;
  description: string;
};

export type CanvasNode = {
  id: string;
  kind: PaletteNodeKind;
  label: string;
  x: number;
  y: number;
};