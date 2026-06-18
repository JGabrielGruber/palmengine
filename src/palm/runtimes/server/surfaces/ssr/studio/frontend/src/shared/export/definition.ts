import type {
  CanvasEdge,
  CanvasNode,
  FlowDefinitionJson,
  ProcessDefinitionJson,
} from "../types";

export type ExportProject = {
  name: string;
  pattern: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
};

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48) || "step";
}

function topologicalOrder(nodes: CanvasNode[], edges: CanvasEdge[]): CanvasNode[] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const indegree = new Map(nodes.map((node) => [node.id, 0]));
  const outgoing = new Map<string, string[]>();

  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) {
      continue;
    }
    indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1);
    const list = outgoing.get(edge.source) ?? [];
    list.push(edge.target);
    outgoing.set(edge.source, list);
  }

  const queue = nodes
    .filter((node) => (indegree.get(node.id) ?? 0) === 0)
    .map((node) => node.id);
  const ordered: CanvasNode[] = [];

  while (queue.length > 0) {
    const id = queue.shift()!;
    const node = byId.get(id);
    if (node) {
      ordered.push(node);
    }
    for (const target of outgoing.get(id) ?? []) {
      const next = (indegree.get(target) ?? 0) - 1;
      indegree.set(target, next);
      if (next === 0) {
        queue.push(target);
      }
    }
  }

  for (const node of nodes) {
    if (!ordered.some((item) => item.id === node.id)) {
      ordered.push(node);
    }
  }
  return ordered;
}

function resolvePattern(project: ExportProject): string {
  const patternNode = project.nodes.find((node) => node.kind === "pattern" && node.ref);
  return patternNode?.ref ?? project.pattern ?? "wizard";
}

function buildWizardSteps(nodes: CanvasNode[]): Record<string, unknown>[] {
  const steps: Record<string, unknown>[] = [];
  for (const node of nodes) {
    if (node.kind === "pattern") {
      continue;
    }
    const slug = slugify(node.ref ?? node.label);
    if (node.kind === "resource" && node.ref) {
      steps.push({
        slug,
        title: node.label,
        step_kind: "resource",
        resource_ref: node.ref,
        output_key: `${slug}_result`,
      });
      continue;
    }
    if (node.kind === "transform" && node.ref) {
      steps.push({
        slug,
        title: node.label,
        step_kind: "transform",
        rule: node.ref,
      });
      continue;
    }
    if (node.kind === "condition") {
      steps.push({
        slug,
        title: node.label,
        step_kind: "condition",
        prompt: node.label,
      });
      continue;
    }
    steps.push({
      slug,
      title: node.label,
      prompt: `Enter ${node.label}`,
      validation: [{ rule: "not_empty" }],
    });
  }
  return steps;
}

function buildPipelineSteps(nodes: CanvasNode[]): Record<string, unknown>[] {
  const steps: Record<string, unknown>[] = [];
  let index = 0;
  for (const node of nodes) {
    if (node.kind !== "transform" || !node.ref) {
      continue;
    }
    index += 1;
    const source = index === 1 ? "input" : `step_${index - 1}`;
    const target = `step_${index}`;
    steps.push({
      name: slugify(node.label),
      source_key: source,
      target_key: target,
      rule: node.ref,
      batch: node.meta?.batch === true,
      options: (node.meta?.options as Record<string, unknown>) ?? {},
    });
  }
  return steps;
}

export function exportFlowDefinition(project: ExportProject): FlowDefinitionJson {
  const pattern = resolvePattern(project);
  const ordered = topologicalOrder(project.nodes, project.edges).filter(
    (node) => node.kind !== "pattern",
  );
  const options: Record<string, unknown> =
    pattern === "pipeline"
      ? { steps: buildPipelineSteps(ordered) }
      : {
          include_summary: true,
          allow_backtrack: true,
          steps: buildWizardSteps(ordered),
        };

  return {
    version: 1,
    kind: "flow",
    name: project.name,
    pattern,
    options,
    id: `flow-${slugify(project.name)}`,
  };
}

export function exportProcessDefinition(project: ExportProject): ProcessDefinitionJson {
  const flow = exportFlowDefinition(project);
  return {
    version: 1,
    kind: "process",
    name: project.name,
    storage: "memory",
    metadata: {
      source: "palm-studio",
      exported_at: new Date().toISOString(),
    },
    flows: [flow],
    id: `proc-${slugify(project.name)}`,
  };
}