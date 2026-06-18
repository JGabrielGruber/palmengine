import type { Core } from "cytoscape";

let cy = $state<Core | undefined>(undefined);
let container = $state<HTMLElement | undefined>(undefined);

export const canvasContext = {
  get cy() {
    return cy;
  },
  get container() {
    return container;
  },
  setCy(value: Core | undefined) {
    cy = value;
  },
  setContainer(value: HTMLElement | undefined) {
    container = value;
  },
};