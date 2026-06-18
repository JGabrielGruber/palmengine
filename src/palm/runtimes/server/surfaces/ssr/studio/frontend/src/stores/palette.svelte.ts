import type { PaletteNode } from "../lib/types";

const palette = $state<PaletteNode[]>([
  {
    id: "action",
    kind: "action",
    label: "Action",
    description: "Execute a behavior-tree action step.",
  },
  {
    id: "condition",
    kind: "condition",
    label: "Condition",
    description: "Branch on a predicate or guard.",
  },
  {
    id: "resource",
    kind: "resource",
    label: "Resource",
    description: "Invoke a registered Palm resource.",
  },
  {
    id: "transform",
    kind: "transform",
    label: "Transform",
    description: "Apply a data transform rule.",
  },
]);

export const paletteStore = {
  get items() {
    return palette;
  },
};