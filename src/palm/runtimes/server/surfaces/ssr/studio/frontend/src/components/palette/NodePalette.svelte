<script lang="ts">
  import type { PaletteNode } from "../../shared/types";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { paletteStore } from "../../stores/palette.svelte";

  const kindAccent: Record<PaletteNode["kind"], string> = {
    action: "border-[#3b82f6]",
    condition: "border-[#f59e0b]",
    resource: "border-[#10b981]",
    transform: "border-[#8b5cf6]",
  };

  function addNode(item: PaletteNode) {
    canvasStore.addFromPalette(item);
  }
</script>

<div class="space-y-2">
  {#each paletteStore.items as item (item.id)}
    <button
      type="button"
      class={`w-full rounded-lg border bg-[#151d2e] p-3 text-left transition hover:bg-[#1a2740] ${kindAccent[item.kind]}`}
      onclick={() => addNode(item)}
    >
      <div class="text-sm font-medium">{item.label}</div>
      <div class="mt-1 text-xs text-[#9aa8c7]">{item.description}</div>
    </button>
  {/each}
</div>