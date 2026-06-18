import { canConnect } from "../shared/canvas/validation";
import { edgeLabel } from "../shared/canvas/nodeTheme";
import type { CanvasEdge, CanvasNode, PaletteItem, StudioCanvas } from "../shared/types";
import { feedbackStore } from "./feedback.svelte";
import { historyStore } from "./history.svelte";
import { projectStore } from "./project.svelte";

let nodes = $state<CanvasNode[]>([]);
let edges = $state<CanvasEdge[]>([]);
let selectedId = $state<string | null>(null);
let counter = 0;

function snapshot(): StudioCanvas {
  return structuredClone({ nodes, edges });
}

function nextId(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}`;
}

function recordHistory() {
  historyStore.record(snapshot());
}

function removeEdgesForNode(id: string) {
  edges = edges.filter((edge) => edge.source !== id && edge.target !== id);
}

function findNode(id: string) {
  return nodes.find((node) => node.id === id);
}

function addEdge(sourceId: string, targetId: string): boolean {
  const check = canConnect(nodes, edges, sourceId, targetId);
  if (!check.ok) {
    feedbackStore.warning(check.message);
    return false;
  }
  const source = findNode(sourceId);
  const target = findNode(targetId);
  if (!source || !target) {
    return false;
  }
  recordHistory();
  edges = [
    ...edges,
    {
      id: nextId("edge"),
      source: sourceId,
      target: targetId,
      label: edgeLabel(source.kind, target.kind),
    },
  ];
  selectedId = targetId;
  feedbackStore.success("Connection created");
  return true;
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
  get canvas() {
    return snapshot();
  },
  select(id: string | null) {
    selectedId = id;
  },
  connect(sourceId: string, targetId: string) {
    return addEdge(sourceId, targetId);
  },
  addFromPalette(item: PaletteItem, position?: { x: number; y: number }) {
    if (!item.draggable) {
      return null;
    }
    recordHistory();
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
    feedbackStore.success(`Added ${item.label}`);
    return node;
  },
  updatePosition(id: string, x: number, y: number) {
    nodes = nodes.map((node) => (node.id === id ? { ...node, x, y } : node));
  },
  commitPosition(id: string, x: number, y: number) {
    recordHistory();
    canvasStore.updatePosition(id, x, y);
  },
  remove(id: string) {
    recordHistory();
    nodes = nodes.filter((node) => node.id !== id);
    removeEdgesForNode(id);
    if (selectedId === id) {
      selectedId = null;
    }
    feedbackStore.info("Node removed");
  },
  removeSelected() {
    if (selectedId) {
      canvasStore.remove(selectedId);
    }
  },
  undo() {
    const previous = historyStore.undo(snapshot());
    if (!previous) {
      return false;
    }
    nodes = previous.nodes;
    edges = previous.edges;
    selectedId = null;
    feedbackStore.info("Undone");
    return true;
  },
  redo() {
    const next = historyStore.redo(snapshot());
    if (!next) {
      return false;
    }
    nodes = next.nodes;
    edges = next.edges;
    selectedId = null;
    feedbackStore.info("Redone");
    return true;
  },
  loadCanvas(snapshotCanvas: StudioCanvas, options?: { record?: boolean }) {
    if (options?.record !== false) {
      recordHistory();
    }
    nodes = snapshotCanvas.nodes ?? [];
    edges = snapshotCanvas.edges ?? [];
    selectedId = null;
    counter = Math.max(
      0,
      ...nodes.map((node) => {
        const match = node.id.match(/-(\d+)$/);
        return match ? Number(match[1]) : 0;
      }),
    );
  },
  replaceCanvas(snapshotCanvas: StudioCanvas) {
    historyStore.clear();
    nodes = snapshotCanvas.nodes ?? [];
    edges = snapshotCanvas.edges ?? [];
    selectedId = null;
    counter = Math.max(
      0,
      ...nodes.map((node) => {
        const match = node.id.match(/-(\d+)$/);
        return match ? Number(match[1]) : 0;
      }),
    );
  },
  reset() {
    recordHistory();
    nodes = [];
    edges = [];
    selectedId = null;
    counter = 0;
  },
};