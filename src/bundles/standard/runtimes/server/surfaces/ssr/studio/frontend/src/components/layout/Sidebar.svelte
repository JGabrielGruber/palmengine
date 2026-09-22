<script lang="ts">
  import type { Snippet } from "svelte";

  type Props = {
    children: Snippet;
  };

  let { children }: Props = $props();
</script>

<div class="flex h-full min-h-0 flex-col">
  <div class="border-b border-[var(--studio-border)] px-4 py-3">
    <h2 class="text-xs font-semibold uppercase tracking-wider text-[var(--studio-muted)]">
      Palette
    </h2>
    <p class="mt-1 text-[11px] text-[var(--studio-muted)]">Drag items onto the canvas</p>
  </div>
  <div class="min-h-0 flex-1 overflow-y-auto p-3">
    {@render children()}
  </div>
</div>