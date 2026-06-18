<script lang="ts">
  import { onMount } from "svelte";
  import type { Core } from "cytoscape";
  import { createGraph, syncNodes } from "../../shared/canvas/cytoscape";
  import { canvasStore } from "../../stores/canvas.svelte";

  let container: HTMLDivElement | undefined = $state();
  let cy: Core | undefined;

  onMount(() => {
    if (!container) {
      return;
    }

    cy = createGraph(container, canvasStore.nodes);

    cy.on("tap", "node", (event) => {
      canvasStore.select(event.target.id());
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        canvasStore.select(null);
      }
    });

    cy.on("dragfree", "node", (event) => {
      const position = event.target.position();
      canvasStore.updatePosition(event.target.id(), position.x, position.y);
    });

    return () => {
      cy?.destroy();
      cy = undefined;
    };
  });

  $effect(() => {
    if (!cy) {
      return;
    }
    syncNodes(cy, canvasStore.nodes);
    if (canvasStore.selectedId) {
      cy.getElementById(canvasStore.selectedId).select();
    } else {
      cy.$(":selected").unselect();
    }
  });
</script>

<div class="absolute inset-0">
  <div
    bind:this={container}
    class="h-full w-full"
    style="background-image: radial-gradient(circle, #1e2a42 1px, transparent 1px); background-size: 24px 24px;"
  ></div>
  <div
    class="pointer-events-none absolute bottom-3 left-3 rounded-md border border-[#2a3a5c] bg-[#0d1526]/90 px-3 py-2 text-xs text-[#9aa8c7]"
  >
    Drag nodes · Click to select · Add from palette
  </div>
</div>