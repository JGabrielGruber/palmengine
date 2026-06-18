<script lang="ts">
  import type { PaletteItem } from "../../shared/types";
  import { importFlowDefinition } from "../../shared/import/definition";
  import { api } from "../../shared/api/client";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { paletteStore } from "../../stores/palette.svelte";
  import { projectStore } from "../../stores/project.svelte";
  import PaletteCard from "./PaletteCard.svelte";

  const DRAG_MIME = "application/palm-studio-palette";

  function onDragStart(item: PaletteItem, event: DragEvent) {
    if (!item.draggable || !event.dataTransfer) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.setData(DRAG_MIME, item.id);
    event.dataTransfer.effectAllowed = "copy";
  }

  async function importFlowItem(item: PaletteItem) {
    if (!item.ref) {
      return;
    }
    try {
      const flow = await api.getFlow(item.ref);
      const imported = importFlowDefinition(flow);
      canvasStore.replaceCanvas({ nodes: imported.nodes, edges: imported.edges });
      projectStore.setName(imported.name);
      projectStore.setPattern(imported.pattern);
      feedbackStore.success(`Imported flow “${imported.name}”`);
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to import flow",
      );
    }
  }
</script>

<div class="space-y-3">
  <div class="sticky top-0 z-10 bg-[#0d1526] pb-2">
    <input
      type="search"
      placeholder="Search palette…"
      class="w-full rounded-lg border border-[#2a3a5c] bg-[#151d2e] px-3 py-2 text-sm text-[#e8edf7] outline-none placeholder:text-[#6b7c9e] focus:border-[#60a5fa]"
      value={paletteStore.query}
      oninput={(event) =>
        paletteStore.setQuery((event.currentTarget as HTMLInputElement).value)}
    />
  </div>

  {#if paletteStore.loading}
    <p class="text-xs text-[#9aa8c7]">Loading palette…</p>
  {:else if paletteStore.error}
    <p class="text-xs text-[#fca5a5]">{paletteStore.error}</p>
  {:else if paletteStore.filteredSections.length === 0}
    <p class="text-xs text-[#9aa8c7]">No palette items match your search.</p>
  {:else}
    {#each paletteStore.filteredSections as section (section.id)}
      <section class="rounded-lg border border-[#1e2a42]/80">
        <button
          type="button"
          class="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-[#151d2e]"
          onclick={() => paletteStore.toggleSection(section.id)}
        >
          <span class="text-[11px] font-semibold uppercase tracking-wider text-[#9aa8c7]">
            {section.label}
          </span>
          <span class="text-xs text-[#6b7c9e]">
            {section.items.length}
            {paletteStore.isCollapsed(section.id) ? "▸" : "▾"}
          </span>
        </button>
        {#if !paletteStore.isCollapsed(section.id)}
          <div class="space-y-2 border-t border-[#1e2a42] p-2">
            {#each section.items as item (item.id)}
              <PaletteCard
                {item}
                {onDragStart}
                onImport={item.kind === "flow" ? importFlowItem : undefined}
              />
            {/each}
          </div>
        {/if}
      </section>
    {/each}
  {/if}
</div>