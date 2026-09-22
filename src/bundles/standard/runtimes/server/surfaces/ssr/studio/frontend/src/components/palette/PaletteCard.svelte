<script lang="ts">
  import { NODE_THEMES } from "../../shared/canvas/nodeTheme";
  import type { PaletteItem } from "../../shared/types";

  type Props = {
    item: PaletteItem;
    onDragStart: (item: PaletteItem, event: DragEvent) => void;
    onImport?: (item: PaletteItem) => void;
  };

  let { item, onDragStart, onImport }: Props = $props();

  const theme = $derived(NODE_THEMES[item.kind]);
</script>

<div
  role="button"
  tabindex="0"
  draggable={item.draggable}
  class={`group rounded-lg border bg-[var(--studio-bg)] p-3 text-left transition ${item.draggable ? "cursor-grab border-[var(--studio-border)] hover:-translate-y-0.5 hover:border-[var(--studio-accent)]/50 hover:bg-[var(--studio-surface-2)] hover:shadow-md active:cursor-grabbing" : "border-[var(--studio-border)]/70 opacity-80"}`}
  style={`border-left: 3px solid ${theme.border};`}
  ondragstart={(event) => onDragStart(item, event)}
>
  <div class="flex items-start gap-2">
    <span
      class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-sm"
      style={`background:${theme.background};color:${theme.accent};`}
    >
      {theme.icon}
    </span>
    <div class="min-w-0 flex-1">
      <div class="flex items-center justify-between gap-2">
        <div class="truncate text-sm font-medium">{item.label}</div>
        <span class="shrink-0 rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-[var(--studio-muted)]">
          {item.kind}
        </span>
      </div>
      <div class="mt-1 line-clamp-2 text-[11px] leading-relaxed text-[var(--studio-muted)]">
        {item.description}
      </div>
      {#if item.ref}
        <div class="mt-1.5 truncate font-mono text-[10px] text-[var(--studio-muted)]">{item.ref}</div>
      {/if}
    </div>
  </div>

  {#if !item.draggable && item.kind === "flow" && onImport}
    <button
      type="button"
      class="mt-2 w-full rounded border border-[var(--studio-border)] px-2 py-1 text-[11px] text-[var(--studio-accent)] opacity-0 transition group-hover:opacity-100 hover:bg-[var(--studio-surface-2)]"
      onclick={() => onImport?.(item)}
    >
      Import to canvas
    </button>
  {/if}
</div>