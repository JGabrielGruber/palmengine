<script lang="ts">
  import { onMount } from "svelte";
  import type { Core } from "cytoscape";
  import {
    createGraph,
    modelPosition,
    pulseSelection,
    syncGraph,
  } from "../../shared/canvas/cytoscape";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { historyStore } from "../../stores/history.svelte";
  import { paletteStore } from "../../stores/palette.svelte";
  import ConnectionHandles from "./ConnectionHandles.svelte";

  const DRAG_MIME = "application/palm-studio-palette";

  let container: HTMLDivElement | undefined = $state();
  let cy: Core | undefined = $state();
  let lastSelected: string | null = null;

  function onKeyDown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    const typing =
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.isContentEditable;

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
      if (typing) {
        return;
      }
      event.preventDefault();
      if (event.shiftKey) {
        canvasStore.redo();
      } else {
        canvasStore.undo();
      }
      return;
    }

    if (event.key === "Escape") {
      canvasStore.select(null);
      return;
    }

    if (event.key === "Delete" || event.key === "Backspace") {
      if (typing) {
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
      canvasStore.select(event.target.id());
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        canvasStore.select(null);
      }
    });

    cy.on("dragfree", "node", (event) => {
      const position = event.target.position();
      canvasStore.commitPosition(event.target.id(), position.x, position.y);
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
      if (canvasStore.selectedId !== lastSelected) {
        pulseSelection(cy, canvasStore.selectedId);
        lastSelected = canvasStore.selectedId;
      }
    } else {
      cy.$(":selected").unselect();
      lastSelected = null;
    }
  });
</script>

<div
  class="absolute inset-0 overflow-hidden"
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

  {#if cy && container}
    <ConnectionHandles {cy} {container} />
  {/if}

  <div
    class="pointer-events-none absolute bottom-3 left-3 rounded-md border border-[#2a3a5c] bg-[#0d1526]/90 px-3 py-2 text-xs text-[#9aa8c7]"
  >
    Drag palette items · Drag blue handles to connect · Ctrl+Z undo
  </div>
</div>