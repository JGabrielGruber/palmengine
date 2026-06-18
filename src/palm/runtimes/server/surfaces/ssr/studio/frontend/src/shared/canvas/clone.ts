import type { StudioCanvas } from "../types";

/** Deep-copy canvas state without structuredClone (Svelte $state proxies are not cloneable). */
export function cloneStudioCanvas(canvas: StudioCanvas): StudioCanvas {
  return {
    nodes: canvas.nodes.map((node) => ({
      ...node,
      meta: node.meta ? { ...node.meta } : undefined,
    })),
    edges: canvas.edges.map((edge) => ({ ...edge })),
    groups: (canvas.groups ?? []).map((group) => ({ ...group })),
  };
}