<script lang="ts">
  import type { Core } from "cytoscape";
  import { onMount } from "svelte";
  import { canvasContext } from "../../stores/canvasContext.svelte";

  const SIZE = 120;
  const PADDING = 8;

  let viewport = $state({ x: 0, y: 0, w: 1, h: 1 });
  let dots = $state<Array<{ x: number; y: number; active: boolean }>>([]);

  function refresh(cy: Core) {
    const nodes = cy.nodes().filter((node) => !node.hasClass("studio-group"));
    if (nodes.length === 0) {
      dots = [];
      return;
    }
    const extent = nodes.boundingBox();
    const width = Math.max(extent.w, 1);
    const height = Math.max(extent.h, 1);
    const innerW = SIZE - PADDING * 2;
    const innerH = SIZE - PADDING * 2;
    const scale = Math.min(innerW / width, innerH / height);

    dots = nodes.map((node) => ({
      x: PADDING + (node.position("x") - extent.x1) * scale,
      y: PADDING + (node.position("y") - extent.y1) * scale,
      active: node.hasClass("sim-active"),
    }));

    const pan = cy.pan();
    const zoom = cy.zoom();
    const rendered = {
      x1: (0 - pan.x) / zoom,
      y1: (0 - pan.y) / zoom,
      x2: (cy.width() - pan.x) / zoom,
      y2: (cy.height() - pan.y) / zoom,
    };
    viewport = {
      x: PADDING + (rendered.x1 - extent.x1) * scale,
      y: PADDING + (rendered.y1 - extent.y1) * scale,
      w: Math.max(12, (rendered.x2 - rendered.x1) * scale),
      h: Math.max(12, (rendered.y2 - rendered.y1) * scale),
    };
  }

  function onMinimapClick(event: MouseEvent) {
    const cy = canvasContext.cy;
    if (!cy) {
      return;
    }
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;
    const nodes = cy.nodes().filter((node) => !node.hasClass("studio-group"));
    if (nodes.length === 0) {
      return;
    }
    const extent = nodes.boundingBox();
    const innerW = SIZE - PADDING * 2;
    const innerH = SIZE - PADDING * 2;
    const scale = Math.min(innerW / Math.max(extent.w, 1), innerH / Math.max(extent.h, 1));
    const modelX = extent.x1 + (clickX - PADDING) / scale;
    const modelY = extent.y1 + (clickY - PADDING) / scale;
    cy.animate({
      pan: {
        x: cy.width() / 2 - modelX * cy.zoom(),
        y: cy.height() / 2 - modelY * cy.zoom(),
      },
      duration: 220,
      easing: "ease-out-cubic",
    });
  }

  onMount(() => {
    const tick = () => {
      const cy = canvasContext.cy;
      if (cy) {
        refresh(cy);
      }
    };
    const interval = window.setInterval(tick, 400);
    return () => clearInterval(interval);
  });
</script>

<button
  type="button"
  class="absolute bottom-3 right-3 z-10 overflow-hidden rounded-lg border border-[var(--studio-border)] bg-[var(--studio-surface)]/95 shadow-lg"
  style={`width:${SIZE}px;height:${SIZE}px`}
  aria-label="Canvas minimap — click to pan"
  onclick={onMinimapClick}
>
  <svg width={SIZE} height={SIZE} class="block">
    {#each dots as dot, index (index)}
      <circle
        cx={dot.x}
        cy={dot.y}
        r={dot.active ? 3.5 : 2.5}
        fill={dot.active ? "var(--studio-accent)" : "var(--studio-muted)"}
      />
    {/each}
    <rect
      x={viewport.x}
      y={viewport.y}
      width={viewport.w}
      height={viewport.h}
      fill="none"
      stroke="var(--studio-accent-soft)"
      stroke-width="1.5"
      rx="2"
    />
  </svg>
</button>