import { edgeLabel } from "../canvas/nodeTheme";
import type {
  CanvasEdge,
  CanvasNode,
  FlowDefinitionJson,
  PaletteNodeKind,
} from "../types";

export type ImportResult = {
  name: string;
  pattern: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
};

const H_SPACING = 180;
const V_CENTER = 180;

function stepKind(step: Record<string, unknown>): PaletteNodeKind {
  const kind = String(step.step_kind ?? "input");
  if (kind === "resource") {
    return "resource";
  }
  if (kind === "transform") {
    return "transform";
  }
  if (kind === "condition") {
    return "condition";
  }
  return "action";
}

function stepLabel(step: Record<string, unknown>): string {
  return String(step.title ?? step.name ?? step.slug ?? "Step");
}

function stepRef(step: Record<string, unknown>, kind: PaletteNodeKind): string | undefined {
  if (kind === "resource") {
    return String(step.resource_ref ?? "");
  }
  if (kind === "transform") {
    return String(step.rule ?? "");
  }
  return undefined;
}

function importWizardSteps(
  steps: Record<string, unknown>[],
  pattern: string,
): ImportResult {
  const nodes: CanvasNode[] = [
    {
      id: "pattern-1",
      kind: "pattern",
      label: pattern,
      ref: pattern,
      x: 80,
      y: V_CENTER,
    },
  ];
  const edges: CanvasEdge[] = [];
  let previousId: string | null = null;

  steps.forEach((step, index) => {
    const kind = stepKind(step);
    const id = `step-${index + 1}`;
    nodes.push({
      id,
      kind,
      label: stepLabel(step),
      ref: stepRef(step, kind),
      x: 80 + (index + 1) * H_SPACING,
      y: V_CENTER,
      meta: { slug: step.slug, imported: true },
    });
    const sourceId = previousId ?? nodes[0].id;
    const sourceNode = nodes.find((node) => node.id === sourceId)!;
    edges.push({
      id: `edge-${index + 1}`,
      source: sourceId,
      target: id,
      label: edgeLabel(sourceNode.kind, kind),
    });
    previousId = id;
  });

  return {
    name: "imported-flow",
    pattern,
    nodes,
    edges,
  };
}

function importPipelineSteps(
  steps: Record<string, unknown>[],
  pattern: string,
): ImportResult {
  const nodes: CanvasNode[] = [
    {
      id: "pattern-1",
      kind: "pattern",
      label: pattern,
      ref: pattern,
      x: 80,
      y: V_CENTER,
    },
  ];
  const edges: CanvasEdge[] = [];
  let previousId = nodes[0].id;

  steps.forEach((step, index) => {
    const id = `step-${index + 1}`;
    const kind: PaletteNodeKind = "transform";
    nodes.push({
      id,
      kind,
      label: String(step.name ?? step.rule ?? `Step ${index + 1}`),
      ref: String(step.rule ?? ""),
      x: 80 + (index + 1) * H_SPACING,
      y: V_CENTER,
      meta: {
        source_key: step.source_key,
        target_key: step.target_key,
        options: step.options,
        batch: step.batch,
        imported: true,
      },
    });
    const sourceNode = nodes.find((node) => node.id === previousId)!;
    edges.push({
      id: `edge-${index + 1}`,
      source: previousId,
      target: id,
      label: edgeLabel(sourceNode.kind, kind),
    });
    previousId = id;
  });

  return {
    name: "imported-flow",
    pattern,
    nodes,
    edges,
  };
}

export function importFlowDefinition(flow: FlowDefinitionJson): ImportResult {
  const pattern = flow.pattern ?? "wizard";
  const options = flow.options ?? {};
  const steps = Array.isArray(options.steps)
    ? (options.steps as Record<string, unknown>[])
    : [];

  const result =
    pattern === "pipeline"
      ? importPipelineSteps(steps, pattern)
      : importWizardSteps(steps, pattern);

  return {
    ...result,
    name: flow.name ?? result.name,
    pattern,
  };
}