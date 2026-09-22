<script lang="ts">
  import { fitBounds, runAutoLayout } from "../../shared/canvas/layout";
  import { panBy, zoomBy } from "../../shared/canvas/cytoscape";
  import { studioEvents } from "../../shared/extensions/events";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { canvasContext } from "../../stores/canvasContext.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";

  function layout(mode: "hierarchical" | "force") {
    const cy = canvasContext.cy;
    if (!cy) {
      return;
    }
    runAutoLayout(cy, mode, (positions) => {
      canvasStore.applyLayoutPositions(positions);
      studioEvents.emit("canvas:layout:applied", { mode });
      feedbackStore.success(
        mode === "hierarchical" ? "Applied hierarchical layout" : "Applied force layout",
      );
    });
  }
</script>

<div
  class="absolute right-3 top-3 z-10 flex flex-col gap-1 rounded-lg border border-[var(--studio-border)] bg-[var(--studio-surface)]/95 p-1 shadow-lg"
  role="toolbar"
  aria-label="Canvas controls"
>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Zoom in (+)"
    onclick={() => canvasContext.cy && zoomBy(canvasContext.cy, 1.15)}
  >
    +
  </button>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Zoom out (-)"
    onclick={() => canvasContext.cy && zoomBy(canvasContext.cy, 0.87)}
  >
    −
  </button>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Fit view (0)"
    onclick={() => canvasContext.cy && fitBounds(canvasContext.cy)}
  >
    Fit
  </button>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Hierarchical layout"
    onclick={() => layout("hierarchical")}
  >
    Tree
  </button>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Force-directed layout"
    onclick={() => layout("force")}
  >
    Flow
  </button>
  <button
    type="button"
    class="rounded px-2 py-1 text-xs hover:bg-[var(--studio-surface-2)]"
    title="Group selected node neighborhood"
    onclick={() => canvasStore.groupSelected("parallel")}
  >
    Group
  </button>
</div>