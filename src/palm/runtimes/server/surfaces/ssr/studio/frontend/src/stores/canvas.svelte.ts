import { cloneStudioCanvas } from "../shared/canvas/clone";
import { edgeLabel } from "../shared/canvas/nodeTheme";
import { groupBounds } from "../shared/canvas/layout";
import { canConnect } from "../shared/canvas/validation";
import { studioEvents } from "../shared/extensions/events";
import type {
  CanvasEdge,
  CanvasGroup,
  CanvasGroupKind,
  CanvasNode,
  PaletteItem,
  StudioCanvas,
} from "../shared/types";
import { feedbackStore } from "./feedback.svelte";
import { historyStore } from "./history.svelte";
import { projectsStore } from "./projects.svelte";

let nodes = $state<CanvasNode[]>([]);
let edges = $state<CanvasEdge[]>([]);
let groups = $state<CanvasGroup[]>([]);
let selectedId = $state<string | null>(null);
let counter = 0;

function snapshot(): StudioCanvas {
  return cloneStudioCanvas({ nodes, edges, groups });
}

function syncProject() {
  projectsStore.updateActiveCanvas(snapshot());
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
  const edge: CanvasEdge = {
    id: nextId("edge"),
    source: sourceId,
    target: targetId,
    label: edgeLabel(source.kind, target.kind),
  };
  edges = [...edges, edge];
  selectedId = targetId;
  syncProject();
  studioEvents.emit("canvas:edge:added", {
    edgeId: edge.id,
    source: sourceId,
    target: targetId,
  });
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
  get groups() {
    return groups;
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
  updateNode(
    id: string,
    patch: Partial<Pick<CanvasNode, "label" | "ref" | "meta">>,
  ) {
    const current = findNode(id);
    if (!current) {
      return false;
    }
    recordHistory();
    nodes = nodes.map((node) =>
      node.id === id
        ? {
            ...node,
            ...patch,
            meta: patch.meta ? { ...node.meta, ...patch.meta } : node.meta,
          }
        : node,
    );
    syncProject();
    return true;
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
      projectsStore.setPattern(item.ref);
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
    syncProject();
    studioEvents.emit("canvas:node:added", { nodeId: node.id });
    feedbackStore.success(`Added ${item.label}`);
    return node;
  },
  updatePosition(id: string, x: number, y: number) {
    nodes = nodes.map((node) => (node.id === id ? { ...node, x, y } : node));
    syncProject();
  },
  applyLayoutPositions(positions: Array<{ id: string; x: number; y: number }>) {
    recordHistory();
    const byId = new Map(positions.map((position) => [position.id, position]));
    nodes = nodes.map((node) => {
      const position = byId.get(node.id);
      return position ? { ...node, x: position.x, y: position.y } : node;
    });
    syncProject();
  },
  commitPosition(id: string, x: number, y: number) {
    recordHistory();
    nodes = nodes.map((node) => (node.id === id ? { ...node, x, y } : node));
    syncProject();
  },
  groupSelected(kind: CanvasGroupKind = "parallel") {
    const selected = canvasStore.selected;
    if (!selected) {
      feedbackStore.warning("Select nodes to group first.");
      return;
    }
    const members = nodes.filter(
      (node) =>
        node.id === selected.id ||
        edges.some(
          (edge) =>
            (edge.source === selected.id && edge.target === node.id) ||
            (edge.target === selected.id && edge.source === node.id),
        ),
    );
    if (members.length < 2) {
      feedbackStore.warning("Select or connect more nodes before grouping.");
      return;
    }
    recordHistory();
    const bounds = groupBounds(members);
    const group: CanvasGroup = {
      ...bounds,
      id: nextId("group"),
      label: kind === "parallel" ? "Parallel" : "Sub-flow",
      kind,
    };
    groups = [...groups, group];
    nodes = nodes.map((node) =>
      members.some((member) => member.id === node.id)
        ? { ...node, parentId: group.id }
        : node,
    );
    syncProject();
    studioEvents.emit("canvas:group:created", { groupId: group.id });
    feedbackStore.success(`Created ${group.label} container`);
  },
  remove(id: string) {
    recordHistory();
    nodes = nodes.filter((node) => node.id !== id);
    nodes = nodes.map((node) =>
      node.parentId === id ? { ...node, parentId: undefined } : node,
    );
    groups = groups.filter((group) => group.id !== id);
    removeEdgesForNode(id);
    if (selectedId === id) {
      selectedId = null;
    }
    syncProject();
    studioEvents.emit("canvas:node:removed", { nodeId: id });
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
    groups = previous.groups ?? [];
    selectedId = null;
    syncProject();
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
    groups = next.groups ?? [];
    selectedId = null;
    syncProject();
    feedbackStore.info("Redone");
    return true;
  },
  loadCanvas(snapshotCanvas: StudioCanvas, options?: { record?: boolean }) {
    if (options?.record !== false) {
      recordHistory();
    }
    nodes = snapshotCanvas.nodes ?? [];
    edges = snapshotCanvas.edges ?? [];
    groups = snapshotCanvas.groups ?? [];
    selectedId = null;
    counter = Math.max(
      0,
      ...nodes.map((node) => {
        const match = node.id.match(/-(\d+)$/);
        return match ? Number(match[1]) : 0;
      }),
    );
    syncProject();
  },
  replaceCanvas(snapshotCanvas: StudioCanvas) {
    historyStore.clear();
    nodes = snapshotCanvas.nodes ?? [];
    edges = snapshotCanvas.edges ?? [];
    groups = snapshotCanvas.groups ?? [];
    selectedId = null;
    counter = Math.max(
      0,
      ...nodes.map((node) => {
        const match = node.id.match(/-(\d+)$/);
        return match ? Number(match[1]) : 0;
      }),
    );
    syncProject();
  },
  reset() {
    recordHistory();
    nodes = [];
    edges = [];
    groups = [];
    selectedId = null;
    counter = 0;
    syncProject();
  },
};