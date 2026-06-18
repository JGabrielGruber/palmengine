<script lang="ts">
  import type { PaletteItem } from "../../shared/types";
  import { paletteStore } from "../../stores/palette.svelte";

  const kindAccent: Record<PaletteItem["kind"], string> = {
    action: "border-l-[#3b82f6]",
    condition: "border-l-[#f59e0b]",
    resource: "border-l-[#10b981]",
    transform: "border-l-[#8b5cf6]",
    pattern: "border-l-[#ec4899]",
    flow: "border-l-[#64748b]",
  };

  const DRAG_MIME = "application/palm-studio-palette";

  function onDragStart(item: PaletteItem, event: DragEvent) {
    if (!item.draggable || !event.dataTransfer) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.setData(DRAG_MIME, item.id);
    event.dataTransfer.effectAllowed = "copy";
  }
</script>

<div class="space-y-4">
  {#if paletteStore.loading}
    <p class="text-xs text-[#9aa8c7]">Loading palette…</p>
  {:else if paletteStore.error}
    <p class="text-xs text-[#fca5a5]">{paletteStore.error}</p>
  {:else}
    {#each paletteStore.sections as section (section.id)}
      <section>
        <h3 class="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#9aa8c7]">
          {section.label}
          <span class="ml-1 text-[#6b7c9e]">({section.items.length})</span>
        </h3>
        <div class="space-y-1.5">
          {#each section.items as item (item.id)}
            <div
              role="button"
              tabindex="0"
              draggable={item.draggable}
              class={`rounded-md border border-[#1e2a42] border-l-4 bg-[#151d2e] p-2.5 text-left transition ${kindAccent[item.kind]} ${item.draggable ? "cursor-grab hover:bg-[#1a2740] active:cursor-grabbing" : "opacity-70"}`}
              ondragstart={(event) => onDragStart(item, event)}
            >
              <div class="text-sm font-medium leading-tight">{item.label}</div>
              <div class="mt-1 line-clamp-2 text-[11px] text-[#9aa8c7]">
                {item.description}
              </div>
              {#if item.ref}
                <div class="mt-1 font-mono text-[10px] text-[#6b7c9e]">{item.ref}</div>
              {/if}
            </div>
          {/each}
        </div>
      </section>
    {/each}
  {/if}
</div>