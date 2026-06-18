import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { NODE_THEMES, nodeDisplayLabel } from "./nodeTheme";
import type { CanvasEdge, CanvasNode, PaletteNodeKind } from "../types";

export function nodeElements(nodes: CanvasNode[]): ElementDefinition[] {
  return nodes.map((node) => ({
    group: "nodes",
    data: {
      id: node.id,
      label: node.label,
      display: nodeDisplayLabel(node.kind, node.label),
      kind: node.kind,
      ref: node.ref ?? "",
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
): Core {
  return cytoscape({
    container,
    elements: [...nodeElements(nodes), ...edgeElements(edges)],
    style: [
      {
        selector: "node",
        style: {
          label: "data(display)",
          "text-valign": "center",
          "text-halign": "center",
          "font-size": 11,
          "font-weight": 500,
          color: "#e8edf7",
          "text-outline-width": 2,
          "text-outline-color": "#0b1220",
          "text-wrap": "wrap",
          "text-max-width": 110,
          width: 148,
          height: 56,
          shape: "round-rectangle",
          "background-color": "#151d2e",
          "border-width": 2,
          "border-color": "#2a3a5c",
          "transition-property": "border-width, border-color, background-color",
          "transition-duration": 180,
        },
      },
      ...Object.keys(NODE_THEMES).map((kind) =>
        kindStyle(kind as PaletteNodeKind),
      ),
      {
        selector: "node:selected",
        style: {
          "border-color": "#60a5fa",
          "background-color": "#1a2740",
          "border-width": 3,
          "overlay-opacity": 0.12,
          "overlay-color": "#60a5fa",
          "overlay-padding": 8,
        },
      },
      {
        selector: "node.connect-target",
        style: {
          "border-color": "#34d399",
          "border-width": 3,
          "overlay-opacity": 0.1,
          "overlay-color": "#34d399",
        },
      },
      {
        selector: "edge",
        style: {
          width: 2,
          "line-color": "#4b5e85",
          "target-arrow-color": "#4b5e85",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "arrow-scale": 0.85,
          label: "data(label)",
          "font-size": 9,
          color: "#9aa8c7",
          "text-background-opacity": 0.85,
          "text-background-color": "#0b1220",
          "text-background-padding": 2,
          "text-border-opacity": 0,
        },
      },
      {
        selector: "edge:selected",
        style: {
          "line-color": "#60a5fa",
          "target-arrow-color": "#60a5fa",
          width: 3,
          color: "#bfdbfe",
        },
      },
    ],
    layout: { name: "preset" },
    minZoom: 0.25,
    maxZoom: 2.5,
    wheelSensitivity: 0.18,
    boxSelectionEnabled: false,
    autoungrabify: false,
  });
}

export function syncGraph(
  cy: Core,
  nodes: CanvasNode[],
  edges: CanvasEdge[],
): void {
  const existingNodes = new Set(cy.nodes().map((node) => node.id()));
  const incomingNodes = new Set(nodes.map((node) => node.id));

  for (const node of nodes) {
    const current = cy.getElementById(node.id);
    if (current.nonempty()) {
      current.position({ x: node.x, y: node.y });
      current.data("label", node.label);
      current.data("display", nodeDisplayLabel(node.kind, node.label));
      current.data("kind", node.kind);
      current.data("ref", node.ref ?? "");
      continue;
    }
    cy.add(nodeElements([node]));
    animateNodeIn(cy, node.id);
  }

  for (const id of existingNodes) {
    if (!incomingNodes.has(id)) {
      cy.getElementById(id).remove();
    }
  }

  const existingEdges = new Set(cy.edges().map((edge) => edge.id()));
  const incomingEdges = new Set(edges.map((edge) => edge.id));

  for (const edge of edges) {
    const current = cy.getElementById(edge.id);
    if (current.nonempty()) {
      current.data("label", edge.label ?? "then");
      continue;
    }
    cy.add(edgeElements([edge]));
  }

  for (const id of existingEdges) {
    if (!incomingEdges.has(id)) {
      cy.getElementById(id).remove();
    }
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
    {
      style: { "border-width": 4 },
      duration: 120,
      easing: "ease-out",
    },
    { queue: true },
  );
  node.animate(
    {
      style: { "border-width": 3 },
      duration: 120,
      easing: "ease-in",
    },
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
  const found = cy.nodes().filter((node) => {
    const box = node.boundingBox({ includeLabels: true });
    return (
      pos.x >= box.x1 && pos.x <= box.x2 && pos.y >= box.y1 && pos.y <= box.y2
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
  if (node.empty()) {
    return null;
  }
  const position = node.renderedPosition();
  const width = node.renderedWidth();
  return {
    x: position.x + width / 2 + 8,
    y: position.y,
  };
}