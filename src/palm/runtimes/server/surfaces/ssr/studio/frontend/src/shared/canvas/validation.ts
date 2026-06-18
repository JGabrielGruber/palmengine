import type { CanvasEdge, CanvasNode } from "../types";

export type ValidationLevel = "warning" | "error";

export type ValidationIssue = {
  id: string;
  level: ValidationLevel;
  message: string;
  nodeId?: string;
  edgeId?: string;
};

export function validateCanvas(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const byId = new Map(nodes.map((node) => [node.id, node]));

  for (const node of nodes) {
    if ((node.kind === "resource" || node.kind === "transform") && !node.ref) {
      issues.push({
        id: `missing-ref-${node.id}`,
        level: "error",
        message: `${node.label} is missing a registry reference.`,
        nodeId: node.id,
      });
    }
  }

  const patternNodes = nodes.filter((node) => node.kind === "pattern");
  if (patternNodes.length > 1) {
    issues.push({
      id: "multiple-patterns",
      level: "warning",
      message: "Multiple pattern nodes found; export uses the first one.",
    });
  }

  for (const edge of edges) {
    const source = byId.get(edge.source);
    const target = byId.get(edge.target);
    if (!source || !target) {
      issues.push({
        id: `dangling-edge-${edge.id}`,
        level: "error",
        message: "Connection references a removed node.",
        edgeId: edge.id,
      });
      continue;
    }
    if (edge.source === edge.target) {
      issues.push({
        id: `self-loop-${edge.id}`,
        level: "error",
        message: "Nodes cannot connect to themselves.",
        edgeId: edge.id,
      });
    }
    if (source.kind === "pattern") {
      issues.push({
        id: `pattern-out-${edge.id}`,
        level: "warning",
        message: "Pattern nodes set flow type; connections from them are ignored on export.",
        edgeId: edge.id,
      });
    }
    if (target.kind === "pattern") {
      issues.push({
        id: `pattern-in-${edge.id}`,
        level: "warning",
        message: "Pattern nodes should not be connection targets.",
        edgeId: edge.id,
      });
    }
  }

  if (nodes.length > 0 && edges.length === 0 && nodes.length > 1) {
    issues.push({
      id: "no-connections",
      level: "warning",
      message: "Nodes have no connections; export order may be arbitrary.",
    });
  }

  const orphans = nodes.filter(
    (node) =>
      node.kind !== "pattern" &&
      !edges.some((edge) => edge.source === node.id || edge.target === node.id),
  );
  if (orphans.length > 1) {
    issues.push({
      id: "orphan-nodes",
      level: "warning",
      message: `${orphans.length} nodes are not connected to the graph.`,
    });
  }

  return issues;
}

export function canConnect(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  sourceId: string,
  targetId: string,
): { ok: true } | { ok: false; message: string } {
  if (sourceId === targetId) {
    return { ok: false, message: "Cannot connect a node to itself." };
  }
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const source = byId.get(sourceId);
  const target = byId.get(targetId);
  if (!source || !target) {
    return { ok: false, message: "Connection endpoints are missing." };
  }
  if (target.kind === "pattern") {
    return { ok: false, message: "Pattern nodes cannot be connection targets." };
  }
  if (
    edges.some((edge) => edge.source === sourceId && edge.target === targetId)
  ) {
    return { ok: false, message: "This connection already exists." };
  }
  return { ok: true };
}