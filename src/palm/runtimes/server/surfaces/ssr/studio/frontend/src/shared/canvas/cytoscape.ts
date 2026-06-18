import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { NODE_THEMES, nodeDisplayLabel } from "./nodeTheme";
import type {
  CanvasEdge,
  CanvasGroup,
  CanvasNode,
  PaletteNodeKind,
} from "../types";

export function groupElements(groups: CanvasGroup[]): ElementDefinition[] {
  return groups.map((group) => ({
    group: "nodes",
    data: {
      id: group.id,
      label: group.label,
      display: group.label,
      kind: "flow",
      ref: group.kind,
    },
    position: { x: group.x, y: group.y },
    classes: "studio-group",
  }));
}

export function nodeElements(nodes: CanvasNode[]): ElementDefinition[] {
  return nodes.map((node) => ({
    group: "nodes",
    data: {
      id: node.id,
      label: node.label,
      display: nodeDisplayLabel(node.kind, node.label),
      kind: node.kind,
      ref: node.ref ?? "",
      parent: node.parentId ?? undefined,
    },
    position: { x: node.x, y: node.y },
  }));
}

export function edgeElements(edges: CanvasEdge[]): ElementDefinition[] {
  return edges.map((edge) => ({
    group: "edges",
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label ?? "then",
    },
  }));
}

function kindStyle(kind: PaletteNodeKind) {
  const theme = NODE_THEMES[kind];
  return {
    selector: `node[kind = "${kind}"]`,
    style: {
      shape: theme.shape,
      "background-color": theme.background,
      "border-color": theme.border,
    },
  };
}

export function createGraph(
  container: HTMLElement,
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  groups: CanvasGroup[] = [],
): Core {
  return cytoscape({
    container,
    elements: [
      ...groupElements(groups),
      ...nodeElements(nodes),
      ...edgeElements(edges),
    ],
    style: [
      {
        selector: "node",
        style: {
          label: "data(display)",
          "text-valign": "center",
          "text-halign": "center",
          "font-size": 11,
          "font-weight": 500,
          color: "var(--studio-text)",
          "text-outline-width": 2,
          "text-outline-color": "var(--studio-bg)",
          "text-wrap": "wrap",
          "text-max-width": 110,
          width: 148,
          height: 56,
          shape: "round-rectangle",
          "background-color": "var(--studio-surface)",
          "border-width": 2,
          "border-color": "var(--studio-border)",
          "transition-property": "border-width, border-color, background-color, opacity",
          "transition-duration": 180,
        },
      },
      {
        selector: "node.studio-group",
        style: {
          label: "data(label)",
          shape: "round-rectangle",
          "background-opacity": 0.12,
          "background-color": "var(--studio-accent)",
          "border-color": "var(--studio-accent-soft)",
          "border-style": "dashed",
          "border-width": 2,
          width: "label",
          height: "label",
          padding: "24px",
          "text-valign": "top",
          "text-halign": "center",
          "font-size": 10,
          color: "var(--studio-accent)",
        },
      },
      ...Object.keys(NODE_THEMES).map((kind) =>
        kindStyle(kind as PaletteNodeKind),
      ),
      {
        selector: "node:selected",
        style: {
          "border-color": "var(--studio-focus)",
          "background-color": "var(--studio-surface-2)",
          "border-width": 3,
          "overlay-opacity": 0.12,
          "overlay-color": "var(--studio-accent)",
          "overlay-padding": 8,
        },
      },
      {
        selector: "node.connect-target",
        style: {
          "border-color": "var(--studio-accent)",
          "border-width": 3,
        },
      },
      {
        selector: "edge",
        style: {
          width: 2,
          "line-color": "var(--studio-border)",
          "target-arrow-color": "var(--studio-accent-soft)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "arrow-scale": 0.85,
          label: "data(label)",
          "font-size": 9,
          color: "var(--studio-muted)",
          "text-background-opacity": 0.9,
          "text-background-color": "var(--studio-bg)",
          "text-background-padding": 2,
        },
      },
      {
        selector: "edge:selected",
        style: {
          "line-color": "var(--studio-focus)",
          "target-arrow-color": "var(--studio-focus)",
          width: 3,
        },
      },
    ],
    layout: { name: "preset" },
    minZoom: 0.15,
    maxZoom: 3,
    wheelSensitivity: 0.2,
    boxSelectionEnabled: false,
    autoungrabify: false,
    userPanningEnabled: true,
    userZoomingEnabled: true,
  });
}

export function syncGraph(
  cy: Core,
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  groups: CanvasGroup[] = [],
): void {
  const desiredIds = new Set([
    ...groups.map((group) => group.id),
    ...nodes.map((node) => node.id),
    ...edges.map((edge) => edge.id),
  ]);
  for (const element of cy.elements()) {
    if (!desiredIds.has(element.id())) {
      element.remove();
    }
  }

  for (const group of groups) {
    const current = cy.getElementById(group.id);
    if (current.nonempty()) {
      current.position({ x: group.x, y: group.y });
      current.data("label", group.label);
      continue;
    }
    cy.add(groupElements([group]));
  }

  for (const node of nodes) {
    const current = cy.getElementById(node.id);
    if (current.nonempty()) {
      current.position({ x: node.x, y: node.y });
      current.data("label", node.label);
      current.data("display", nodeDisplayLabel(node.kind, node.label));
      current.data("kind", node.kind);
      current.data("ref", node.ref ?? "");
      if (node.parentId) {
        current.move({ parent: node.parentId });
      } else {
        current.move({ parent: null });
      }
      continue;
    }
    cy.add(nodeElements([node]));
    animateNodeIn(cy, node.id);
  }

  for (const edge of edges) {
    const current = cy.getElementById(edge.id);
    if (current.nonempty()) {
      current.data("label", edge.label ?? "then");
      continue;
    }
    cy.add(edgeElements([edge]));
  }
}

export function animateNodeIn(cy: Core, nodeId: string) {
  const node = cy.getElementById(nodeId);
  if (node.empty()) {
    return;
  }
  node.style({ opacity: 0.2 });
  node.animate(
    { style: { opacity: 1 }, duration: 220, easing: "ease-out-cubic" },
    { queue: true },
  );
}

export function pulseSelection(cy: Core, nodeId: string | null) {
  if (!nodeId) {
    return;
  }
  const node = cy.getElementById(nodeId);
  if (node.empty()) {
    return;
  }
  node.animate(
    { style: { "border-width": 4 }, duration: 120, easing: "ease-out" },
    { queue: true },
  );
  node.animate(
    { style: { "border-width": 3 }, duration: 120, easing: "ease-in" },
    { queue: true },
  );
}

export function modelPosition(
  cy: Core,
  container: HTMLElement,
  clientX: number,
  clientY: number,
): { x: number; y: number } {
  const rect = container.getBoundingClientRect();
  return cy.renderer().renderedToModelPosition({
    x: clientX - rect.left,
    y: clientY - rect.top,
  });
}

export function nodeAtPoint(
  cy: Core,
  container: HTMLElement,
  clientX: number,
  clientY: number,
): string | null {
  const pos = modelPosition(cy, container, clientX, clientY);
  const found = cy
    .nodes()
    .filter((node) => !node.hasClass("studio-group"))
    .filter((node) => {
      const box = node.boundingBox({ includeLabels: true });
      return (
        pos.x >= box.x1 &&
        pos.x <= box.x2 &&
        pos.y >= box.y1 &&
        pos.y <= box.y2
      );
    });
  return found.length > 0 ? found[0].id() : null;
}

export function renderedHandlePosition(
  cy: Core,
  _container: HTMLElement,
  nodeId: string,
): { x: number; y: number } | null {
  const node = cy.getElementById(nodeId);
  if (node.empty() || node.hasClass("studio-group")) {
    return null;
  }
  const position = node.renderedPosition();
  const width = node.renderedWidth();
  return {
    x: position.x + width / 2 + 8,
    y: position.y,
  };
}

export function panBy(cy: Core, dx: number, dy: number) {
  const pan = cy.pan();
  cy.pan({ x: pan.x + dx, y: pan.y + dy });
}

export function zoomBy(cy: Core, factor: number) {
  const level = cy.zoom();
  cy.zoom({
    level: Math.min(3, Math.max(0.15, level * factor)),
    renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
  });
}