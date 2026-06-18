<script lang="ts">
  import { onMount } from "svelte";
  import type { Core } from "cytoscape";
  import {
    createGraph,
    modelPosition,
    panBy,
    pulseSelection,
    syncGraph,
    zoomBy,
  } from "../../shared/canvas/cytoscape";
  import { shortcuts } from "../../shared/keyboard/shortcuts";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { canvasContext } from "../../stores/canvasContext.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { paletteStore } from "../../stores/palette.svelte";
  import { projectsStore } from "../../stores/projects.svelte";
  import CanvasControls from "./CanvasControls.svelte";
  import ConnectionHandles from "./ConnectionHandles.svelte";

  const DRAG_MIME = "application/palm-studio-palette";

  let container: HTMLDivElement | undefined = $state();
  let cy: Core | undefined = $state();
  let lastSelected: string | null = null;
  let loadedProjectId = $state<string | null>(null);

  function onKeyDown(event: KeyboardEvent) {
    if (shortcuts.handle(event)) {
      return;
    }
    const target = event.target as HTMLElement;
    const typing =
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.isContentEditable;
    if (typing) {
      return;
    }
    const instance = canvasContext.cy;
    if (!instance) {
      return;
    }
    if (event.key === "Escape") {
      canvasStore.select(null);
      return;
    }
    if (event.key === "Delete" || event.key === "Backspace") {
      event.preventDefault();
      canvasStore.removeSelected();
      return;
    }
    const step = event.shiftKey ? 48 : 24;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      panBy(instance, step, 0);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      panBy(instance, -step, 0);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      panBy(instance, 0, step);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      panBy(instance, 0, -step);
    } else if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      zoomBy(instance, 1.12);
    } else if (event.key === "-") {
      event.preventDefault();
      zoomBy(instance, 0.9);
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

  $effect(() => {
    const project = projectsStore.active;
    if (loadedProjectId === project.id) {
      return;
    }
    canvasStore.replaceCanvas(project.canvas);
    loadedProjectId = project.id;
  });

  onMount(() => {
    paletteStore.load();
    draftStore.restoreLocal();

    const unregister = [
      shortcuts.register({
        id: "undo",
        keys: "ctrl+z",
        description: "Undo",
        handler: () => canvasStore.undo(),
      }),
      shortcuts.register({
        id: "redo",
        keys: "ctrl+shift+z",
        description: "Redo",
        handler: () => canvasStore.redo(),
      }),
      shortcuts.register({
        id: "save",
        keys: "ctrl+s",
        description: "Save draft",
        handler: () => draftStore.saveLocal(),
      }),
    ];

    if (!container) {
      return () => unregister.forEach((off) => off());
    }

    cy = createGraph(
      container,
      canvasStore.nodes,
      canvasStore.edges,
      canvasStore.groups,
    );
    canvasContext.setCy(cy);
    canvasContext.setContainer(container);

    cy.on("tap", "node", (event) => {
      if (event.target.hasClass("studio-group")) {
        return;
      }
      canvasStore.select(event.target.id());
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        canvasStore.select(null);
      }
    });

    cy.on("dragfree", "node", (event) => {
      if (event.target.hasClass("studio-group")) {
        return;
      }
      const position = event.target.position();
      canvasStore.commitPosition(event.target.id(), position.x, position.y);
    });

    window.addEventListener("keydown", onKeyDown);

    return () => {
      unregister.forEach((off) => off());
      window.removeEventListener("keydown", onKeyDown);
      canvasContext.setCy(undefined);
      canvasContext.setContainer(undefined);
      cy?.destroy();
      cy = undefined;
    };
  });

  $effect(() => {
    if (!cy) {
      return;
    }
    syncGraph(cy, canvasStore.nodes, canvasStore.edges, canvasStore.groups);
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
  tabindex="0"
  ondragover={(event) => event.preventDefault()}
  ondrop={onDrop}
>
  <div
    bind:this={container}
    class="h-full w-full"
    style="background-image: radial-gradient(circle, var(--studio-border) 1px, transparent 1px); background-size: 24px 24px;"
  ></div>

  <CanvasControls />

  {#if cy && container}
    <ConnectionHandles {cy} {container} />
  {/if}

  <div
    class="pointer-events-none absolute bottom-3 left-3 rounded-md border border-[var(--studio-border)] bg-[var(--studio-surface)]/90 px-3 py-2 text-xs text-[var(--studio-muted)]"
  >
    Arrows pan · +/- zoom · Drag handles to connect · Ctrl+Z undo
  </div>
</div>