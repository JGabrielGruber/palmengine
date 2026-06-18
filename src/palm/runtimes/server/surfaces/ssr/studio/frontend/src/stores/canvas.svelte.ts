import type { CanvasNode, PaletteNode } from "../shared/types";

let nodes = $state<CanvasNode[]>([
  { id: "start", kind: "action", label: "Start", x: 120, y: 120 },
  { id: "step-1", kind: "resource", label: "Fetch Data", x: 320, y: 120 },
  { id: "end", kind: "action", label: "Complete", x: 520, y: 120 },
]);

let selectedId = $state<string | null>(null);

let counter = 0;

export const canvasStore = {
  get nodes() {
    return nodes;
  },
  get selectedId() {
    return selectedId;
  },
  get selected() {
    return nodes.find((node) => node.id === selectedId) ?? null;
  },
  select(id: string | null) {
    selectedId = id;
  },
  addFromPalette(palette: PaletteNode, position?: { x: number; y: number }) {
    counter += 1;
    const node: CanvasNode = {
      id: `${palette.kind}-${counter}`,
      kind: palette.kind,
      label: palette.label,
      x: position?.x ?? 200 + counter * 24,
      y: position?.y ?? 200 + counter * 16,
    };
    nodes = [...nodes, node];
    selectedId = node.id;
    return node;
  },
  updatePosition(id: string, x: number, y: number) {
    nodes = nodes.map((node) => (node.id === id ? { ...node, x, y } : node));
  },
  remove(id: string) {
    nodes = nodes.filter((node) => node.id !== id);
    if (selectedId === id) {
      selectedId = null;
    }
  },
};