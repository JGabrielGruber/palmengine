<script lang="ts">
  import { canvasStore } from "../../stores/canvas.svelte";

  const selected = $derived(canvasStore.selected);
  const incoming = $derived(
    selected
      ? canvasStore.edges.filter((edge) => edge.target === selected.id)
      : [],
  );
  const outgoing = $derived(
    selected
      ? canvasStore.edges.filter((edge) => edge.source === selected.id)
      : [],
  );
</script>

<aside class="flex min-h-0 flex-col overflow-hidden">
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
        {#if selected.ref}
          <div>
            <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Ref</dt>
            <dd class="mt-1 font-mono text-xs">{selected.ref}</dd>
          </div>
        {/if}
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Position</dt>
          <dd class="mt-1 font-mono text-xs">
            x {Math.round(selected.x)}, y {Math.round(selected.y)}
          </dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-[#9aa8c7]">Connections</dt>
          <dd class="mt-1 space-y-1 text-xs text-[#9aa8c7]">
            <div>Incoming: {incoming.length}</div>
            <div>Outgoing: {outgoing.length}</div>
          </dd>
        </div>
      </dl>

      <div class="mt-5 space-y-2">
        <button
          type="button"
          class="w-full rounded-md border border-[#2a3a5c] bg-[#151d2e] px-3 py-2 text-xs hover:bg-[#1a2740]"
          onclick={() => canvasStore.beginConnect(selected.id)}
        >
          Connect to another node
        </button>
        <button
          type="button"
          class="w-full rounded-md border border-[#7f1d1d] bg-[#1a1010] px-3 py-2 text-xs text-[#fca5a5] hover:bg-[#2a1515]"
          onclick={() => canvasStore.remove(selected.id)}
        >
          Remove node
        </button>
      </div>
    {:else}
      <p class="text-[#9aa8c7]">
        Select a node on the canvas to inspect properties, create connections, or
        remove it.
      </p>
    {/if}
  </div>
</aside>