import type { StudioCanvas } from "../shared/types";

const MAX_HISTORY = 50;

let past = $state<StudioCanvas[]>([]);
let future = $state<StudioCanvas[]>([]);

function cloneCanvas(canvas: StudioCanvas): StudioCanvas {
  return structuredClone(canvas);
}

export const historyStore = {
  get canUndo() {
    return past.length > 0;
  },
  get canRedo() {
    return future.length > 0;
  },
  record(canvas: StudioCanvas) {
    past = [...past.slice(-(MAX_HISTORY - 1)), cloneCanvas(canvas)];
    future = [];
  },
  undo(current: StudioCanvas): StudioCanvas | null {
    if (past.length === 0) {
      return null;
    }
    const previous = past[past.length - 1];
    past = past.slice(0, -1);
    future = [cloneCanvas(current), ...future];
    return cloneCanvas(previous);
  },
  redo(current: StudioCanvas): StudioCanvas | null {
    if (future.length === 0) {
      return null;
    }
    const [next, ...rest] = future;
    future = rest;
    past = [...past, cloneCanvas(current)];
    return cloneCanvas(next);
  },
  clear() {
    past = [];
    future = [];
  },
};