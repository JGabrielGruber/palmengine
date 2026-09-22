<script lang="ts">
  import type { PaletteItem } from "../../shared/types";
  import { importFlowDefinition } from "../../shared/import/definition";
  import { api } from "../../shared/api/client";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { paletteStore } from "../../stores/palette.svelte";
  import { projectsStore } from "../../stores/projects.svelte";
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
      canvasStore.replaceCanvas({
        nodes: imported.nodes,
        edges: imported.edges,
        groups: [],
      });
      projectsStore.replaceActive({
        name: imported.name,
        pattern: imported.pattern,
        canvas: { nodes: imported.nodes, edges: imported.edges, groups: [] },
      });
      feedbackStore.success(`Imported flow “${imported.name}”`);
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to import flow",
      );
    }
  }
</script>

<div class="space-y-3">
  <div class="sticky top-0 z-10 bg-[var(--studio-surface)] pb-2">
    <input
      type="search"
      placeholder="Search palette…"
      class="w-full rounded-lg border border-[var(--studio-border)] bg-[var(--studio-bg)] px-3 py-2 text-sm text-[var(--studio-text)] outline-none placeholder:text-[var(--studio-muted)] focus:border-[var(--studio-accent)]"
      value={paletteStore.query}
      oninput={(event) =>
        paletteStore.setQuery((event.currentTarget as HTMLInputElement).value)}
    />
  </div>

  {#if paletteStore.loading}
    <p class="text-xs text-[var(--studio-muted)]">Loading palette…</p>
  {:else if paletteStore.error}
    <p class="text-xs text-[var(--studio-rose)]">{paletteStore.error}</p>
  {:else if paletteStore.filteredSections.length === 0}
    <p class="text-xs text-[var(--studio-muted)]">No palette items match your search.</p>
  {:else}
    {#each paletteStore.filteredSections as section (section.id)}
      <section class="rounded-lg border border-[var(--studio-border)]/80">
        <button
          type="button"
          class="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-[var(--studio-surface-2)]"
          onclick={() => paletteStore.toggleSection(section.id)}
        >
          <span class="text-[11px] font-semibold uppercase tracking-wider text-[var(--studio-muted)]">
            {section.label}
          </span>
          <span class="text-xs text-[var(--studio-muted)]">
            {section.items.length}
            {paletteStore.isCollapsed(section.id) ? "▸" : "▾"}
          </span>
        </button>
        {#if !paletteStore.isCollapsed(section.id)}
          <div class="space-y-2 border-t border-[var(--studio-border)] p-2">
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