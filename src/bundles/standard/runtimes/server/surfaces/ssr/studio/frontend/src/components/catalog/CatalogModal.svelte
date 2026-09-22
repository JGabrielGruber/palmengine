<script lang="ts">
  import { importFlowDefinition } from "../../shared/import/definition";
  import { importProcessDefinition } from "../../shared/import/process";
  import { api } from "../../shared/api/client";
  import { studio } from "../../shared/theme/classes";
  import type { FlowSummary, ProcessSummary } from "../../shared/types";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { projectsStore } from "../../stores/projects.svelte";

  type Props = {
    open: boolean;
    onClose: () => void;
  };

  let { open, onClose }: Props = $props();

  type CatalogTab = "flows" | "processes";
  let tab = $state<CatalogTab>("flows");
  let flows = $state<FlowSummary[]>([]);
  let processes = $state<ProcessSummary[]>([]);
  let selectedId = $state("");
  let loading = $state(false);

  async function loadCatalog() {
    loading = true;
    try {
      const [flowResponse, processResponse] = await Promise.all([
        api.listFlows(),
        api.listProcesses(),
      ]);
      flows = flowResponse.flows;
      processes = processResponse.processes;
      selectedId =
        tab === "flows"
          ? (flows[0]?.flow_id ?? "")
          : (processes[0]?.process_id ?? "");
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to load catalog",
      );
      onClose();
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if (open) {
      void loadCatalog();
    }
  });

  $effect(() => {
    if (!open) {
      return;
    }
    selectedId =
      tab === "flows"
        ? (flows[0]?.flow_id ?? "")
        : (processes[0]?.process_id ?? "");
  });

  async function openSelected() {
    if (!selectedId) {
      return;
    }
    loading = true;
    try {
      if (tab === "flows") {
        const flow = await api.getFlow(selectedId);
        const imported = importFlowDefinition(flow);
        projectsStore.openInNewTab({
          name: imported.name,
          pattern: imported.pattern,
          canvas: {
            nodes: imported.nodes,
            edges: imported.edges,
            groups: [],
          },
        });
        feedbackStore.success(`Opened flow “${imported.name}” in new tab`);
      } else {
        const process = await api.getProcess(selectedId);
        const imported = importProcessDefinition(process);
        projectsStore.openInNewTab({
          name: imported.name,
          pattern: imported.pattern,
          canvas: {
            nodes: imported.nodes,
            edges: imported.edges,
            groups: [],
          },
        });
        feedbackStore.success(`Opened process “${imported.name}” in new tab`);
      }
      onClose();
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to open from catalog",
      );
    } finally {
      loading = false;
    }
  }
</script>

{#if open}
  <div
    class="absolute inset-0 z-30 flex items-center justify-center bg-black/60 p-4"
    role="dialog"
    aria-modal="true"
    aria-label="Definition catalog"
  >
    <div
      class="flex max-h-[85%] w-full max-w-xl flex-col overflow-hidden rounded-xl border border-[var(--studio-border)] bg-[var(--studio-surface)] shadow-2xl"
    >
      <div class="flex items-center justify-between border-b border-[var(--studio-border)] px-4 py-3">
        <div>
          <h3 class="text-sm font-semibold">Open from catalog</h3>
          <p class="text-xs text-[var(--studio-muted)]">
            Load a registered flow or process into a new project tab
          </p>
        </div>
        <button type="button" class="rounded px-2 py-1 text-sm hover:bg-[var(--studio-surface-2)]" onclick={onClose}>
          ✕
        </button>
      </div>

      <div class="flex gap-1 border-b border-[var(--studio-border)] px-4 py-2">
        <button
          type="button"
          class={`rounded px-3 py-1 text-xs ${tab === "flows" ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
          onclick={() => (tab = "flows")}
        >
          Flows ({flows.length})
        </button>
        <button
          type="button"
          class={`rounded px-3 py-1 text-xs ${tab === "processes" ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
          onclick={() => (tab = "processes")}
        >
          Processes ({processes.length})
        </button>
      </div>

      <div class="min-h-0 flex-1 overflow-y-auto p-4">
        {#if loading && (tab === "flows" ? flows.length === 0 : processes.length === 0)}
          <p class="text-xs text-[var(--studio-muted)]">Loading catalog…</p>
        {:else if tab === "flows"}
          <select class="{studio.input} w-full py-2" bind:value={selectedId}>
            {#each flows as flow (flow.flow_id)}
              <option value={flow.flow_id}>
                {flow.name} ({flow.pattern})
              </option>
            {/each}
          </select>
        {:else}
          <select class="{studio.input} w-full py-2" bind:value={selectedId}>
            {#each processes as process (process.process_id)}
              <option value={process.process_id}>
                {process.name} ({process.flow_count} flows)
              </option>
            {/each}
          </select>
        {/if}
      </div>

      <div class="flex justify-end gap-2 border-t border-[var(--studio-border)] px-4 py-3">
        <button type="button" class={studio.btn} onclick={onClose}>Cancel</button>
        <button
          type="button"
          class="{studio.btnAccent} disabled:opacity-40"
          disabled={loading || !selectedId}
          onclick={openSelected}
        >
          Open in new tab
        </button>
      </div>
    </div>
  </div>
{/if}