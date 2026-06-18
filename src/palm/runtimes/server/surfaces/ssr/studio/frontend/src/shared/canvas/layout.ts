import type { Core } from "cytoscape";
import type { CanvasGroup, CanvasNode } from "../types";

export type LayoutMode = "hierarchical" | "force";

export function runAutoLayout(
  cy: Core,
  mode: LayoutMode,
  onComplete?: (positions: Array<{ id: string; x: number; y: number }>) => void,
) {
  const layout = cy.layout({
    name: mode === "hierarchical" ? "breadthfirst" : "cose",
    directed: true,
    fit: true,
    padding: 48,
    spacingFactor: 1.2,
    animate: true,
    animationDuration: 420,
    animationEasing: "ease-out-cubic",
  });

  layout.on("layoutstop", () => {
    const positions = cy
      .nodes()
      .filter((node) => !node.isParent())
      .map((node) => ({
        id: node.id(),
        x: node.position("x"),
        y: node.position("y"),
      }));
    onComplete?.(positions);
  });

  layout.run();
}

export function fitBounds(cy: Core) {
  cy.animate({ fit: { easing: "ease-out-cubic", padding: 48 }, duration: 220 });
}

export function groupBounds(nodes: CanvasNode[]): CanvasGroup {
  const padding = 48;
  const xs = nodes.map((node) => node.x);
  const ys = nodes.map((node) => node.y);
  const minX = Math.min(...xs) - padding;
  const maxX = Math.max(...xs) + padding;
  const minY = Math.min(...ys) - padding;
  const maxY = Math.max(...ys) + padding;
  return {
    id: `group-${Date.now()}`,
    label: "Group",
    kind: "parallel",
    x: (minX + maxX) / 2,
    y: (minY + maxY) / 2,
    width: Math.max(180, maxX - minX),
    height: Math.max(120, maxY - minY),
  };
}