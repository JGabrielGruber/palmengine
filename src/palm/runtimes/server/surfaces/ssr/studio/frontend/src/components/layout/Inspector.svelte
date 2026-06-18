<script lang="ts">
  import { NODE_THEMES } from "../../shared/canvas/nodeTheme";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { validationStore } from "../../stores/validation.svelte";

  const selected = $derived(canvasStore.selected);
  const theme = $derived(selected ? NODE_THEMES[selected.kind] : null);
  const nodeIssues = $derived(
    selected
      ? validationStore.issues.filter((issue) => issue.nodeId === selected.id)
      : [],
  );
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
  <div class="border-b border-[var(--studio-border)] px-4 py-3">
    <h2 class="text-xs font-semibold uppercase tracking-wider text-[var(--studio-muted)]">
      Inspector
    </h2>
  </div>
  <div class="min-h-0 flex-1 overflow-y-auto p-4 text-sm">
    {#if validationStore.issues.length > 0 && !selected}
      <section class="mb-4 rounded-lg border border-[var(--studio-border)] bg-[var(--studio-bg)] p-3">
        <h3 class="text-xs font-semibold uppercase tracking-wide text-[var(--studio-muted)]">
          Validation
        </h3>
        <ul class="mt-2 space-y-1.5 text-xs">
          {#each validationStore.issues as issue (issue.id)}
            <li class={issue.level === "error" ? "text-[var(--studio-rose)]" : "text-[var(--studio-amber)]"}>
              {issue.message}
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    {#if selected && theme}
      <div
        class="mb-4 flex items-center gap-2 rounded-lg border border-[var(--studio-border)] p-3"
        style={`border-left:3px solid ${theme.border};background:${theme.background}`}
      >
        <span class="text-lg">{theme.icon}</span>
        <div>
          <div class="font-medium">{selected.label}</div>
          <div class="text-xs capitalize text-[var(--studio-muted)]">{selected.kind}</div>
        </div>
      </div>

      <dl class="space-y-3">
        <div>
          <dt class="text-xs uppercase tracking-wide text-[var(--studio-muted)]">ID</dt>
          <dd class="mt-1 font-mono text-xs">{selected.id}</dd>
        </div>
        {#if selected.ref}
          <div>
            <dt class="text-xs uppercase tracking-wide text-[var(--studio-muted)]">Ref</dt>
            <dd class="mt-1 font-mono text-xs">{selected.ref}</dd>
          </div>
        {/if}
        <div>
          <dt class="text-xs uppercase tracking-wide text-[var(--studio-muted)]">Position</dt>
          <dd class="mt-1 font-mono text-xs">
            x {Math.round(selected.x)}, y {Math.round(selected.y)}
          </dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-[var(--studio-muted)]">Connections</dt>
          <dd class="mt-1 space-y-1 text-xs text-[var(--studio-muted)]">
            <div>In: {incoming.map((edge) => edge.label ?? "then").join(", ") || "—"}</div>
            <div>Out: {outgoing.map((edge) => edge.label ?? "then").join(", ") || "—"}</div>
          </dd>
        </div>
      </dl>

      {#if nodeIssues.length > 0}
        <ul class="mt-4 space-y-1 text-xs">
          {#each nodeIssues as issue (issue.id)}
            <li class={issue.level === "error" ? "text-[var(--studio-rose)]" : "text-[var(--studio-amber)]"}>
              {issue.message}
            </li>
          {/each}
        </ul>
      {/if}

      <div class="mt-5">
        <button
          type="button"
          class="w-full rounded-md border border-[var(--studio-rose)]/40 bg-[var(--studio-bg)] px-3 py-2 text-xs text-[var(--studio-rose)] hover:bg-[var(--studio-surface-2)]"
          onclick={() => canvasStore.remove(selected.id)}
        >
          Remove node
        </button>
      </div>
    {:else if !validationStore.issues.length}
      <p class="text-[var(--studio-muted)]">
        Select a node to inspect it. Drag the blue handle on a node to create
        connections.
      </p>
    {/if}
  </div>
</aside>