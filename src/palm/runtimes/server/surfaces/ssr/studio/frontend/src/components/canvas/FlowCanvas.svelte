<script lang="ts">
  import { onMount } from "svelte";
  import type { Core } from "cytoscape";
  import {
    createGraph,
    modelPosition,
    syncGraph,
  } from "../../shared/canvas/cytoscape";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { paletteStore } from "../../stores/palette.svelte";

  const DRAG_MIME = "application/palm-studio-palette";

  let container: HTMLDivElement | undefined = $state();
  let cy: Core | undefined;

  function handleNodeTap(id: string) {
    if (canvasStore.isConnectMode) {
      canvasStore.completeConnect(id);
      return;
    }
    canvasStore.select(id);
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      canvasStore.cancelConnect();
      canvasStore.select(null);
      return;
    }
    if (event.key === "Delete" || event.key === "Backspace") {
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
        return;
      }
      event.preventDefault();
      canvasStore.removeSelected();
    }
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    if (!cy || !container || !event.dataTransfer) {
      return;
    }
    const itemId = event.dataTransfer.getData(DRAG_MIME);
    const item = paletteStore.findItem(itemId);
    if (!item) {
      return;
    }
    const position = modelPosition(cy, container, event.clientX, event.clientY);
    canvasStore.addFromPalette(item, position);
  }

  onMount(() => {
    paletteStore.load();
    draftStore.restoreLocal();

    if (!container) {
      return;
    }

    cy = createGraph(container, canvasStore.nodes, canvasStore.edges);

    cy.on("tap", "node", (event) => {
      handleNodeTap(event.target.id());
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        if (canvasStore.isConnectMode) {
          canvasStore.cancelConnect();
        }
        canvasStore.select(null);
      }
    });

    cy.on("dragfree", "node", (event) => {
      const position = event.target.position();
      canvasStore.updatePosition(event.target.id(), position.x, position.y);
    });

    window.addEventListener("keydown", onKeyDown);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      cy?.destroy();
      cy = undefined;
    };
  });

  $effect(() => {
    if (!cy) {
      return;
    }
    syncGraph(cy, canvasStore.nodes, canvasStore.edges);
    if (canvasStore.selectedId) {
      cy.getElementById(canvasStore.selectedId).select();
    } else {
      cy.$(":selected").unselect();
    }
  });
</script>

<div
  class="absolute inset-0"
  role="application"
  aria-label="Flow canvas"
  ondragover={(event) => event.preventDefault()}
  ondrop={onDrop}
>
  <div
    bind:this={container}
    class="h-full w-full"
    style="background-image: radial-gradient(circle, #1e2a42 1px, transparent 1px); background-size: 24px 24px;"
  ></div>
  <div
    class="pointer-events-none absolute bottom-3 left-3 rounded-md border border-[#2a3a5c] bg-[#0d1526]/90 px-3 py-2 text-xs text-[#9aa8c7]"
  >
    {#if canvasStore.isConnectMode}
      Click a target node to connect · Esc to cancel
    {:else}
      Drag from palette · Select node · Del to remove · Inspector to connect
    {/if}
  </div>
</div>