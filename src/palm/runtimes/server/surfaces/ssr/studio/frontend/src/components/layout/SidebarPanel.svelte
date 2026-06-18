<script lang="ts">
  import NodePalette from "../palette/NodePalette.svelte";
  import TemplateGallery from "../templates/TemplateGallery.svelte";

  type PanelTab = "palette" | "templates";
  let tab = $state<PanelTab>("palette");
</script>

<div class="flex h-full min-h-0 flex-col">
  <div class="flex gap-1 border-b border-[var(--studio-border)] px-3 py-2">
    <button
      type="button"
      role="tab"
      aria-selected={tab === "palette"}
      class={`rounded px-3 py-1 text-xs ${tab === "palette" ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
      onclick={() => (tab = "palette")}
    >
      Palette
    </button>
    <button
      type="button"
      role="tab"
      aria-selected={tab === "templates"}
      class={`rounded px-3 py-1 text-xs ${tab === "templates" ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
      onclick={() => (tab = "templates")}
    >
      Templates
    </button>
  </div>

  <div class="min-h-0 flex-1 overflow-y-auto p-3">
    {#if tab === "palette"}
      <NodePalette />
    {:else}
      <TemplateGallery />
    {/if}
  </div>
</div>