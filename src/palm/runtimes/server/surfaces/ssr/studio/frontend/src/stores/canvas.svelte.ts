import type { CanvasEdge, CanvasNode, PaletteItem } from "../shared/types";
import { projectStore } from "./project.svelte";

let nodes = $state<CanvasNode[]>([]);
let edges = $state<CanvasEdge[]>([]);
let selectedId = $state<string | null>(null);
let connectSourceId = $state<string | null>(null);
let counter = 0;

function nextId(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}`;
}

function removeEdgesForNode(id: string) {
  edges = edges.filter((edge) => edge.source !== id && edge.target !== id);
}

export const canvasStore = {
  get nodes() {
    return nodes;
  },
  get edges() {
    return edges;
  },
  get selectedId() {
    return selectedId;
  },
  get selected() {
    return nodes.find((node) => node.id === selectedId) ?? null;
  },
  get connectSourceId() {
    return connectSourceId;
  },
  get isConnectMode() {
    return connectSourceId !== null;
  },
  select(id: string | null) {
    selectedId = id;
  },
  beginConnect(id: string) {
    connectSourceId = id;
    selectedId = id;
  },
  cancelConnect() {
    connectSourceId = null;
  },
  completeConnect(targetId: string) {
    if (!connectSourceId || connectSourceId === targetId) {
      connectSourceId = null;
      return;
    }
    const exists = edges.some(
      (edge) => edge.source === connectSourceId && edge.target === targetId,
    );
    if (!exists) {
      edges = [
        ...edges,
        { id: nextId("edge"), source: connectSourceId, target: targetId },
      ];
    }
    connectSourceId = null;
    selectedId = targetId;
  },
  addFromPalette(item: PaletteItem, position?: { x: number; y: number }) {
    if (!item.draggable) {
      return null;
    }
    if (item.kind === "pattern" && item.ref) {
      projectStore.setPattern(item.ref);
    }
    const node: CanvasNode = {
      id: nextId(item.kind),
      kind: item.kind,
      label: item.label,
      ref: item.ref,
      x: position?.x ?? 180 + counter * 28,
      y: position?.y ?? 160 + counter * 22,
      meta: {
        provider: item.provider,
        action: item.action,
        mode: item.mode,
      },
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
    removeEdgesForNode(id);
    if (selectedId === id) {
      selectedId = null;
    }
    if (connectSourceId === id) {
      connectSourceId = null;
    }
  },
  removeSelected() {
    if (selectedId) {
      canvasStore.remove(selectedId);
    }
  },
  loadCanvas(snapshot: { nodes?: CanvasNode[]; edges?: CanvasEdge[] }) {
    nodes = snapshot.nodes ?? [];
    edges = snapshot.edges ?? [];
    selectedId = null;
    connectSourceId = null;
    counter = Math.max(
      0,
      ...nodes.map((node) => {
        const match = node.id.match(/-(\d+)$/);
        return match ? Number(match[1]) : 0;
      }),
    );
  },
  reset() {
    nodes = [];
    edges = [];
    selectedId = null;
    connectSourceId = null;
    counter = 0;
  },
};