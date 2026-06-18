import { resolveSimulationTrace } from "../shared/simulate/trace";
import type { JobContext } from "../shared/types";
import { canvasStore } from "./canvas.svelte";

let active = $state(false);
let jobId = $state<string | null>(null);
let context = $state<JobContext | null>(null);

export const simulationStore = {
  get active() {
    return active;
  },
  get jobId() {
    return jobId;
  },
  get context() {
    return context;
  },
  get trace() {
    return resolveSimulationTrace(canvasStore.nodes, context);
  },
  start(id: string) {
    active = true;
    jobId = id;
    context = null;
  },
  updateContext(next: JobContext) {
    context = next;
  },
  stop() {
    active = false;
    jobId = null;
    context = null;
  },
};