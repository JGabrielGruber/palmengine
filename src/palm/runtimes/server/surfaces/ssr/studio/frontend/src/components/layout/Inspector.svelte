<script lang="ts">
  import { canvasStore } from "../../stores/canvas.svelte";

  const selected = $derived(canvasStore.selected);
</script>

<aside class="flex min-h-0 flex-col overflow-hidden bg-[#0d1526]">
  <div class="border-b border-[#1e2a42] px-4 py-3">
    <h2 class="text-xs font-semibold uppercase tracking-wider text-[#9aa8c7]">
      Inspector
    </h2>
  </div>
  <div class="min-h-0 flex-1 overflow-y-auto p-4 text-sm">
    {#if selected}
      <dl class="space-y-3">
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">ID</dt>
          <dd class="mt-1 font-mono text-xs">{selected.id}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Label</dt>
          <dd class="mt-1">{selected.label}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Kind</dt>
          <dd class="mt-1 capitalize">{selected.kind}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Position</dt>
          <dd class="mt-1 font-mono text-xs">
            x {Math.round(selected.x)}, y {Math.round(selected.y)}
          </dd>
        </div>
      </dl>
      <button
        type="button"
        class="mt-6 w-full rounded-md border border-[#7f1d1d] bg-[#1a1010] px-3 py-2 text-xs text-[#fca5a5] hover:bg-[#2a1515]"
        onclick={() => canvasStore.remove(selected.id)}
      >
        Remove node
      </button>
    {:else}
      <p class="text-[#9aa8c7]">
        Select a node on the canvas to inspect its properties.
      </p>
    {/if}
  </div>
</aside>