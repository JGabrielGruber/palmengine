import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import type { CanvasNode } from "../types";

const KIND_COLORS: Record<CanvasNode["kind"], string> = {
  action: "#3b82f6",
  condition: "#f59e0b",
  resource: "#10b981",
  transform: "#8b5cf6",
};

export function nodeElements(nodes: CanvasNode[]): ElementDefinition[] {
  return nodes.map((node) => ({
    group: "nodes",
    data: { id: node.id, label: node.label, kind: node.kind },
    position: { x: node.x, y: node.y },
  }));
}

export function createGraph(container: HTMLElement, nodes: CanvasNode[]): Core {
  return cytoscape({
    container,
    elements: nodeElements(nodes),
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
          width: 120,
          height: 48,
          shape: "round-rectangle",
          "background-color": "#151d2e",
          "border-width": 2,
          "border-color": "#2a3a5c",
        },
      },
      {
        selector: 'node[kind = "action"]',
        style: { "border-color": KIND_COLORS.action },
      },
      {
        selector: 'node[kind = "condition"]',
        style: { "border-color": KIND_COLORS.condition },
      },
      {
        selector: 'node[kind = "resource"]',
        style: { "border-color": KIND_COLORS.resource },
      },
      {
        selector: 'node[kind = "transform"]',
        style: { "border-color": KIND_COLORS.transform },
      },
      {
        selector: "node:selected",
        style: {
          "border-color": "#60a5fa",
          "background-color": "#1a2740",
        },
      },
    ],
    layout: { name: "preset" },
    minZoom: 0.3,
    maxZoom: 2,
    wheelSensitivity: 0.2,
  });
}

export function syncNodes(cy: Core, nodes: CanvasNode[]): void {
  const existing = new Set(cy.nodes().map((node) => node.id()));
  const incoming = new Set(nodes.map((node) => node.id));

  for (const node of nodes) {
    const current = cy.getElementById(node.id);
    if (current.nonempty()) {
      current.position({ x: node.x, y: node.y });
      current.data("label", node.label);
      current.data("kind", node.kind);
      continue;
    }
    cy.add(nodeElements([node]));
  }

  for (const id of existing) {
    if (!incoming.has(id)) {
      cy.getElementById(id).remove();
    }
  }
}