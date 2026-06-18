import { validateCanvas } from "../shared/canvas/validation";
import { canvasStore } from "./canvas.svelte";

export const validationStore = {
  get issues() {
    return validateCanvas(canvasStore.nodes, canvasStore.edges);
  },
  get errorCount() {
    return validationStore.issues.filter((issue) => issue.level === "error").length;
  },
  get warningCount() {
    return validationStore.issues.filter((issue) => issue.level === "warning").length;
  },
};