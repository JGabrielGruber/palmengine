import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import type { CanvasEdge, CanvasNode, PaletteNodeKind } from "../types";

const KIND_COLORS: Record<PaletteNodeKind, string> = {
  action: "#3b82f6",
  condition: "#f59e0b",
  resource: "#10b981",
  transform: "#8b5cf6",
  pattern: "#ec4899",
  flow: "#64748b",
};

export function nodeElements(nodes: CanvasNode[]): ElementDefinition[] {
  return nodes.map((node) => ({
    group: "nodes",
    data: { id: node.id, label: node.label, kind: node.kind, ref: node.ref ?? "" },
    position: { x: node.x, y: node.y },
  }));
}

export function edgeElements(edges: CanvasEdge[]): ElementDefinition[] {
  return edges.map((edge) => ({
    group: "edges",
    data: { id: edge.id, source: edge.source, target: edge.target },
  }));
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
          label: "data(label)",
          "text-valign": "center",
          "text-halign": "center",
          "font-size": 11,
          color: "#e8edf7",
          "text-outline-width": 2,
          "text-outline-color": "#0b1220",
          width: 132,
          height: 52,
          shape: "round-rectangle",
          "background-color": "#151d2e",
          "border-width": 2,
          "border-color": "#2a3a5c",
        },
      },
      ...Object.entries(KIND_COLORS).map(([kind, color]) => ({
        selector: `node[kind = "${kind}"]`,
        style: { "border-color": color },
      })),
      {
        selector: "node:selected",
        style: {
          "border-color": "#60a5fa",
          "background-color": "#1a2740",
          "border-width": 3,
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
          "arrow-scale": 0.9,
        },
      },
      {
        selector: "edge:selected",
        style: {
          "line-color": "#60a5fa",
          "target-arrow-color": "#60a5fa",
          width: 3,
        },
      },
    ],
    layout: { name: "preset" },
    minZoom: 0.25,
    maxZoom: 2.5,
    wheelSensitivity: 0.18,
    boxSelectionEnabled: false,
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
      current.data("kind", node.kind);
      current.data("ref", node.ref ?? "");
      continue;
    }
    cy.add(nodeElements([node]));
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