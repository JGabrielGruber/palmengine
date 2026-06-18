<script lang="ts">
  import type { Snippet } from "svelte";

  type Props = {
    children: Snippet;
  };

  let { children }: Props = $props();
</script>

<div class="flex h-full min-h-0 flex-col">
  <div class="border-b border-[#1e2a42] px-4 py-3">
    <h2 class="text-xs font-semibold uppercase tracking-wider text-[#9aa8c7]">
      Palette
    </h2>
    <p class="mt-1 text-[11px] text-[#6b7c9e]">Drag items onto the canvas</p>
  </div>
  <div class="min-h-0 flex-1 overflow-y-auto p-3">
    {@render children()}
  </div>
</div>