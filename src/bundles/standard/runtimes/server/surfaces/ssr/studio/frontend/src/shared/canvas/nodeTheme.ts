import type { PaletteNodeKind } from "../types";

export type NodeTheme = {
  icon: string;
  shape:
    | "round-rectangle"
    | "diamond"
    | "hexagon"
    | "ellipse"
    | "tag"
    | "barrel";
  background: string;
  border: string;
  accent: string;
};

export const NODE_THEMES: Record<PaletteNodeKind, NodeTheme> = {
  action: {
    icon: "▶",
    shape: "round-rectangle",
    background: "#132238",
    border: "#3b82f6",
    accent: "#60a5fa",
  },
  condition: {
    icon: "◇",
    shape: "diamond",
    background: "#2a2010",
    border: "#f59e0b",
    accent: "#fbbf24",
  },
  resource: {
    icon: "⬡",
    shape: "hexagon",
    background: "#102820",
    border: "#10b981",
    accent: "#34d399",
  },
  transform: {
    icon: "⚙",
    shape: "barrel",
    background: "#1f1533",
    border: "#8b5cf6",
    accent: "#a78bfa",
  },
  pattern: {
    icon: "◆",
    shape: "tag",
    background: "#2a1020",
    border: "#ec4899",
    accent: "#f472b6",
  },
  flow: {
    icon: "⎋",
    shape: "ellipse",
    background: "#151d2e",
    border: "#64748b",
    accent: "#94a3b8",
  },
};

export function nodeDisplayLabel(kind: PaletteNodeKind, label: string): string {
  const icon = NODE_THEMES[kind].icon;
  const trimmed = label.length > 14 ? `${label.slice(0, 12)}…` : label;
  return `${icon} ${trimmed}`;
}

export function edgeLabel(sourceKind: PaletteNodeKind, targetKind: PaletteNodeKind): string {
  if (sourceKind === "condition") {
    return "yes";
  }
  if (targetKind === "transform") {
    return "map";
  }
  if (targetKind === "resource") {
    return "invoke";
  }
  return "then";
}