<script lang="ts">
  import type { Core } from "cytoscape";
  import { nodeAtPoint, renderedHandlePosition } from "../../shared/canvas/cytoscape";
  import { canvasStore } from "../../stores/canvas.svelte";

  type Props = {
    cy: Core;
    container: HTMLElement;
  };

  let { cy, container }: Props = $props();

  let handles = $state<Array<{ id: string; x: number; y: number }>>([]);
  let draggingFrom = $state<string | null>(null);
  let pointer = $state<{ x: number; y: number } | null>(null);
  let hoverTarget = $state<string | null>(null);

  function refreshHandles() {
    handles = canvasStore.nodes
      .map((node) => {
        const position = renderedHandlePosition(cy, container, node.id);
        return position ? { id: node.id, ...position } : null;
      })
      .filter((entry): entry is { id: string; x: number; y: number } => entry !== null);
  }

  function onPointerMove(event: PointerEvent) {
    if (!draggingFrom) {
      return;
    }
    pointer = { x: event.clientX, y: event.clientY };
    hoverTarget = nodeAtPoint(cy, container, event.clientX, event.clientY);
    cy.nodes().removeClass("connect-target");
    if (hoverTarget && hoverTarget !== draggingFrom) {
      cy.getElementById(hoverTarget).addClass("connect-target");
    }
  }

  function stopDragging(event: PointerEvent) {
    if (!draggingFrom) {
      return;
    }
    const targetId = nodeAtPoint(cy, container, event.clientX, event.clientY);
    if (targetId && targetId !== draggingFrom) {
      canvasStore.connect(draggingFrom, targetId);
    }
    draggingFrom = null;
    pointer = null;
    hoverTarget = null;
    cy.nodes().removeClass("connect-target");
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", stopDragging);
  }

  function startDrag(nodeId: string, event: PointerEvent) {
    event.preventDefault();
    event.stopPropagation();
    draggingFrom = nodeId;
    pointer = { x: event.clientX, y: event.clientY };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", stopDragging);
  }

  $effect(() => {
    canvasStore.nodes;
    canvasStore.selectedId;
    refreshHandles();
    const onViewport = () => refreshHandles();
    cy.on("pan zoom position dragfree", onViewport);
    return () => {
      cy.off("pan zoom position dragfree", onViewport);
    };
  });
</script>

{#each handles as handle (handle.id)}
  <button
    type="button"
    aria-label={`Connect from ${handle.id}`}
    class="absolute z-10 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#60a5fa] bg-[#0b1220] shadow transition hover:scale-125 hover:bg-[#1a2740]"
    style={`left:${handle.x}px;top:${handle.y}px;`}
    onpointerdown={(event) => startDrag(handle.id, event)}
  ></button>
{/each}

{#if draggingFrom && pointer}
  {@const rect = container.getBoundingClientRect()}
  {@const origin = handles.find((handle) => handle.id === draggingFrom)}
  {#if origin}
    <svg class="pointer-events-none absolute inset-0 z-[5] h-full w-full">
      <line
        x1={origin.x}
        y1={origin.y}
        x2={pointer.x - rect.left}
        y2={pointer.y - rect.top}
        stroke="#60a5fa"
        stroke-width="2"
        stroke-dasharray="6 4"
      />
    </svg>
  {/if}
{/if}