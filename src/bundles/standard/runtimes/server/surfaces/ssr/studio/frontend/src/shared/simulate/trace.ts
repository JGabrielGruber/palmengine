import { nodeStepSlug } from "../canvas/slug";
import type { CanvasNode, JobContext } from "../types";

export type SimulationTrace = {
  activeNodeIds: string[];
  completedNodeIds: string[];
  activeStep: string | null;
};

export function resolveSimulationTrace(
  nodes: CanvasNode[],
  context: JobContext | null,
): SimulationTrace {
  if (!context) {
    return { activeNodeIds: [], completedNodeIds: [], activeStep: null };
  }

  const progress = context.wizard_progress ?? {};
  const activeStep =
    (typeof progress.current_step === "string" && progress.current_step) ||
    context.pattern?.step ||
    null;
  const completedRaw = progress.completed_steps;
  const completedSteps = Array.isArray(completedRaw)
    ? completedRaw.map(String)
    : [];

  const bySlug = new Map<string, CanvasNode>();
  for (const node of nodes) {
    if (node.kind === "pattern") {
      continue;
    }
    bySlug.set(nodeStepSlug(node), node);
  }

  const activeNodeIds: string[] = [];
  const completedNodeIds: string[] = [];

  if (activeStep && bySlug.has(activeStep)) {
    activeNodeIds.push(bySlug.get(activeStep)!.id);
  }

  for (const slug of completedSteps) {
    const node = bySlug.get(slug);
    if (node && !activeNodeIds.includes(node.id)) {
      completedNodeIds.push(node.id);
    }
  }

  return { activeNodeIds, completedNodeIds, activeStep };
}