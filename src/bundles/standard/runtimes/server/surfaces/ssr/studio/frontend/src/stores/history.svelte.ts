import { cloneStudioCanvas } from "../shared/canvas/clone";
import type { StudioCanvas } from "../shared/types";

const MAX_HISTORY = 50;

let past = $state<StudioCanvas[]>([]);
let future = $state<StudioCanvas[]>([]);

export const historyStore = {
  get canUndo() {
    return past.length > 0;
  },
  get canRedo() {
    return future.length > 0;
  },
  record(canvas: StudioCanvas) {
    past = [...past.slice(-(MAX_HISTORY - 1)), cloneStudioCanvas(canvas)];
    future = [];
  },
  undo(current: StudioCanvas): StudioCanvas | null {
    if (past.length === 0) {
      return null;
    }
    const previous = past[past.length - 1];
    past = past.slice(0, -1);
    future = [cloneStudioCanvas(current), ...future];
    return cloneStudioCanvas(previous);
  },
  redo(current: StudioCanvas): StudioCanvas | null {
    if (future.length === 0) {
      return null;
    }
    const [next, ...rest] = future;
    future = rest;
    past = [...past, cloneStudioCanvas(current)];
    return cloneStudioCanvas(next);
  },
  clear() {
    past = [];
    future = [];
  },
};