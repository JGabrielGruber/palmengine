<script lang="ts">
  import {
    exportFlowDefinition,
    exportProcessDefinition,
  } from "../../shared/export/definition";
  import { importFlowDefinition } from "../../shared/import/definition";
  import { api } from "../../shared/api/client";
  import type { FlowSummary } from "../../shared/types";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { historyStore } from "../../stores/history.svelte";
  import { projectStore } from "../../stores/project.svelte";
  import { validationStore } from "../../stores/validation.svelte";

  let exportText = $state<string | null>(null);
  let showExport = $state(false);
  let showImport = $state(false);
  let flows = $state<FlowSummary[]>([]);
  let importLoading = $state(false);
  let selectedFlowId = $state("");

  async function saveDraft(localOnly = false) {
    try {
      if (localOnly) {
        draftStore.saveLocal();
        feedbackStore.success("Draft saved locally");
      } else {
        await draftStore.saveServer();
      }
    } catch {
      /* surfaced via feedback */
    }
  }

  function openExport(kind: "flow" | "process") {
    if (validationStore.errorCount > 0) {
      feedbackStore.warning("Fix validation errors before exporting.");
      return;
    }
    const project = {
      name: projectStore.name,
      pattern: projectStore.pattern,
      nodes: canvasStore.nodes,
      edges: canvasStore.edges,
    };
    const payload =
      kind === "flow"
        ? exportFlowDefinition(project)
        : exportProcessDefinition(project);
    exportText = JSON.stringify(payload, null, 2);
    showExport = true;
  }

  async function openImport() {
    showImport = true;
    importLoading = true;
    try {
      const response = await api.listFlows();
      flows = response.flows;
      selectedFlowId = response.flows[0]?.flow_id ?? "";
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to list flows",
      );
      showImport = false;
    } finally {
      importLoading = false;
    }
  }

  async function confirmImport() {
    if (!selectedFlowId) {
      return;
    }
    importLoading = true;
    try {
      const flow = await api.getFlow(selectedFlowId);
      const imported = importFlowDefinition(flow);
      canvasStore.replaceCanvas({ nodes: imported.nodes, edges: imported.edges });
      projectStore.setName(imported.name);
      projectStore.setPattern(imported.pattern);
      showImport = false;
      feedbackStore.success(`Imported “${imported.name}”`);
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to import flow",
      );
    } finally {
      importLoading = false;
    }
  }

  async function copyExport() {
    if (!exportText) {
      return;
    }
    await navigator.clipboard.writeText(exportText);
    feedbackStore.success("Copied to clipboard");
  }

  function downloadExport() {
    if (!exportText) {
      return;
    }
    const blob = new Blob([exportText], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectStore.name}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="flex flex-wrap items-center gap-2 border-b border-[#1e2a42] px-4 py-2">
  <label class="flex items-center gap-2 text-xs text-[#9aa8c7]">
    Flow name
    <input
      class="rounded-md border border-[#2a3a5c] bg-[#151d2e] px-2 py-1 text-sm text-[#e8edf7] outline-none focus:border-[#60a5fa]"
      value={projectStore.name}
      oninput={(event) =>
        projectStore.setName((event.currentTarget as HTMLInputElement).value)}
    />
  </label>

  <span class="rounded-full border border-[#2a3a5c] px-2 py-0.5 text-xs text-[#9aa8c7]">
    pattern: {projectStore.pattern}
  </span>

  {#if validationStore.warningCount > 0 || validationStore.errorCount > 0}
    <span
      class={`rounded-full px-2 py-0.5 text-xs ${validationStore.errorCount > 0 ? "border border-[#7f1d1d] text-[#fca5a5]" : "border border-[#713f12] text-[#fcd34d]"}`}
    >
      {validationStore.errorCount} errors · {validationStore.warningCount} warnings
    </span>
  {/if}

  <div class="ml-auto flex flex-wrap items-center gap-2">
    <button
      type="button"
      class="rounded-md border border-[#2a3a5c] px-2 py-1.5 text-xs disabled:opacity-40"
      disabled={!historyStore.canUndo}
      onclick={() => canvasStore.undo()}
      title="Undo (Ctrl+Z)"
    >
      Undo
    </button>
    <button
      type="button"
      class="rounded-md border border-[#2a3a5c] px-2 py-1.5 text-xs disabled:opacity-40"
      disabled={!historyStore.canRedo}
      onclick={() => canvasStore.redo()}
      title="Redo (Ctrl+Shift+Z)"
    >
      Redo
    </button>
    <button
      type="button"
      class="rounded-md border border-[#2a3a5c] px-3 py-1.5 text-xs hover:bg-[#151d2e]"
      onclick={openImport}
    >
      Import flow
    </button>
    <button
      type="button"
      class="rounded-md border border-[#2a3a5c] px-3 py-1.5 text-xs hover:bg-[#151d2e]"
      onclick={() => saveDraft(true)}
    >
      Save draft
    </button>
    <button
      type="button"
      class="rounded-md border border-[#2a3a5c] px-3 py-1.5 text-xs hover:bg-[#151d2e]"
      onclick={() => saveDraft(false)}
    >
      Save to server
    </button>
    <button
      type="button"
      class="rounded-md bg-[#1a2740] px-3 py-1.5 text-xs text-[#93c5fd] hover:bg-[#243352]"
      onclick={() => openExport("flow")}
    >
      Export flow
    </button>
    <button
      type="button"
      class="rounded-md bg-[#1e3a2f] px-3 py-1.5 text-xs text-[#86efac] hover:bg-[#264d3f]"
      onclick={() => openExport("process")}
    >
      Export process
    </button>
  </div>
</div>

{#if showImport}
  <div
    class="absolute inset-x-4 top-20 z-20 max-w-lg overflow-hidden rounded-lg border border-[#2a3a5c] bg-[#0d1526] shadow-2xl"
  >
    <div class="border-b border-[#1e2a42] px-4 py-3">
      <h3 class="text-sm font-medium">Import flow</h3>
      <p class="mt-1 text-xs text-[#9aa8c7]">
        Load a registered flow from the server onto the canvas.
      </p>
    </div>
    <div class="space-y-3 p-4">
      {#if importLoading && flows.length === 0}
        <p class="text-xs text-[#9aa8c7]">Loading flows…</p>
      {:else}
        <select
          class="w-full rounded-md border border-[#2a3a5c] bg-[#151d2e] px-2 py-2 text-sm"
          bind:value={selectedFlowId}
        >
          {#each flows as flow (flow.flow_id)}
            <option value={flow.flow_id}>
              {flow.name} ({flow.pattern})
            </option>
          {/each}
        </select>
      {/if}
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="rounded border border-[#2a3a5c] px-3 py-1 text-xs"
          onclick={() => (showImport = false)}
        >
          Cancel
        </button>
        <button
          type="button"
          class="rounded bg-[#1a2740] px-3 py-1 text-xs text-[#93c5fd] disabled:opacity-40"
          disabled={importLoading || !selectedFlowId}
          onclick={confirmImport}
        >
          Import
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showExport && exportText}
  <div
    class="absolute inset-x-4 top-20 z-20 max-h-[70%] overflow-hidden rounded-lg border border-[#2a3a5c] bg-[#0d1526] shadow-2xl"
  >
    <div class="flex items-center justify-between border-b border-[#1e2a42] px-4 py-2">
      <h3 class="text-sm font-medium">Exported definition</h3>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded border border-[#2a3a5c] px-2 py-1 text-xs"
          onclick={copyExport}
        >
          Copy
        </button>
        <button
          type="button"
          class="rounded border border-[#2a3a5c] px-2 py-1 text-xs"
          onclick={downloadExport}
        >
          Download
        </button>
        <button
          type="button"
          class="rounded border border-[#2a3a5c] px-2 py-1 text-xs"
          onclick={() => (showExport = false)}
        >
          Close
        </button>
      </div>
    </div>
    <pre class="overflow-auto p-4 text-xs text-[#cbd5e1]">{exportText}</pre>
  </div>
{/if}