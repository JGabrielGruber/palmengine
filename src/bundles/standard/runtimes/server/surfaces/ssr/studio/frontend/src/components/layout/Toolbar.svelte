<script lang="ts">
  import {
    exportFlowDefinition,
    exportProcessDefinition,
  } from "../../shared/export/definition";
  import { importFlowDefinition } from "../../shared/import/definition";
  import CatalogModal from "../catalog/CatalogModal.svelte";
  import { api } from "../../shared/api/client";
  import { studio } from "../../shared/theme/classes";
  import type { FlowSummary } from "../../shared/types";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { historyStore } from "../../stores/history.svelte";
  import { projectStore, projectsStore } from "../../stores/projects.svelte";
  import { validationStore } from "../../stores/validation.svelte";

  type Props = {
    onSimulate?: () => void;
  };

  let { onSimulate }: Props = $props();

  let exportText = $state<string | null>(null);
  let showExport = $state(false);
  let showImport = $state(false);
  let showCatalog = $state(false);
  let flows = $state<FlowSummary[]>([]);
  let importLoading = $state(false);
  let selectedFlowId = $state("");

  async function saveDraft(localOnly = false) {
    try {
      if (localOnly) {
        draftStore.saveLocal();
      } else {
        await draftStore.saveServer();
      }
    } catch {
      /* surfaced via feedback */
    }
  }

  function projectPayload() {
    return {
      name: projectStore.name,
      pattern: projectStore.pattern,
      nodes: canvasStore.nodes,
      edges: canvasStore.edges,
    };
  }

  async function saveAsFlow() {
    if (validationStore.errorCount > 0) {
      feedbackStore.warning("Fix validation errors before saving.");
      return;
    }
    try {
      const flow = exportFlowDefinition(projectPayload());
      await feedbackStore.run("Saving flow to catalog", () => api.saveFlow(flow));
    } catch {
      /* surfaced via feedback */
    }
  }

  async function saveAsProcess() {
    if (validationStore.errorCount > 0) {
      feedbackStore.warning("Fix validation errors before saving.");
      return;
    }
    try {
      const process = exportProcessDefinition(projectPayload());
      await feedbackStore.run("Saving process to catalog", () =>
        api.saveProcess(process),
      );
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
      projectsStore.replaceActive({
        name: imported.name,
        pattern: imported.pattern,
        canvas: { nodes: imported.nodes, edges: imported.edges, groups: [] },
      });
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

<div class="flex flex-wrap items-center gap-2 border-b border-[var(--studio-border)] px-4 py-2">
  <label class="flex items-center gap-2 text-xs text-[var(--studio-muted)]">
    Flow name
    <input
      class={studio.input}
      value={projectStore.name}
      oninput={(event) =>
        projectStore.setName((event.currentTarget as HTMLInputElement).value)}
    />
  </label>

  <span class="rounded-full border border-[var(--studio-border)] px-2 py-0.5 text-xs text-[var(--studio-muted)]">
    pattern: {projectStore.pattern}
  </span>
  <span class="rounded-full border border-[var(--studio-border)] px-2 py-0.5 text-xs text-[var(--studio-muted)]">
    draft v{projectStore.draftVersion}
  </span>

  {#if validationStore.warningCount > 0 || validationStore.errorCount > 0}
    <span
      class={`rounded-full px-2 py-0.5 text-xs ${validationStore.errorCount > 0 ? "border border-[var(--studio-rose)]/40 text-[var(--studio-rose)]" : "border border-[var(--studio-amber)]/40 text-[var(--studio-amber)]"}`}
    >
      {validationStore.errorCount} errors · {validationStore.warningCount} warnings
    </span>
  {/if}

  <div class="ml-auto flex flex-wrap items-center gap-2">
    <button
      type="button"
      class="{studio.btn} disabled:opacity-40"
      disabled={!historyStore.canUndo}
      onclick={() => canvasStore.undo()}
      title="Undo (Ctrl+Z)"
    >
      Undo
    </button>
    <button
      type="button"
      class="{studio.btn} disabled:opacity-40"
      disabled={!historyStore.canRedo}
      onclick={() => canvasStore.redo()}
      title="Redo (Ctrl+Shift+Z)"
    >
      Redo
    </button>
    <button type="button" class={studio.btn} onclick={() => onSimulate?.()}>
      Simulate
    </button>
    <button type="button" class={studio.btn} onclick={() => (showCatalog = true)}>
      Open catalog
    </button>
    <button type="button" class={studio.btn} onclick={openImport}>
      Import flow
    </button>
    <button type="button" class="{studio.btn} text-[var(--studio-accent)]" onclick={saveAsFlow}>
      Save as flow
    </button>
    <button type="button" class="{studio.btn} text-[var(--studio-accent)]" onclick={saveAsProcess}>
      Save as process
    </button>
    <button type="button" class={studio.btn} onclick={() => saveDraft(true)}>
      Save draft
    </button>
    <button type="button" class={studio.btn} onclick={() => saveDraft(false)}>
      Save to server
    </button>
    <button type="button" class="{studio.btn} text-[var(--studio-accent)]" onclick={() => openExport("flow")}>
      Export flow
    </button>
    <button type="button" class="{studio.btn} text-[var(--studio-accent)]" onclick={() => openExport("process")}>
      Export process
    </button>
  </div>
</div>

{#if showImport}
  <div
    class="absolute inset-x-4 top-20 z-20 max-w-lg overflow-hidden rounded-lg border border-[var(--studio-border)] bg-[var(--studio-surface)] shadow-2xl"
  >
    <div class="border-b border-[var(--studio-border)] px-4 py-3">
      <h3 class="text-sm font-medium">Import flow</h3>
      <p class="mt-1 text-xs text-[var(--studio-muted)]">
        Load a registered flow from the server onto the canvas.
      </p>
    </div>
    <div class="space-y-3 p-4">
      {#if importLoading && flows.length === 0}
        <p class="text-xs text-[var(--studio-muted)]">Loading flows…</p>
      {:else}
        <select class="{studio.input} w-full py-2" bind:value={selectedFlowId}>
          {#each flows as flow (flow.flow_id)}
            <option value={flow.flow_id}>
              {flow.name} ({flow.pattern})
            </option>
          {/each}
        </select>
      {/if}
      <div class="flex justify-end gap-2">
        <button type="button" class={studio.btn} onclick={() => (showImport = false)}>
          Cancel
        </button>
        <button
          type="button"
          class="{studio.btnAccent} disabled:opacity-40"
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
    class="absolute inset-x-4 top-20 z-20 max-h-[70%] overflow-hidden rounded-lg border border-[var(--studio-border)] bg-[var(--studio-surface)] shadow-2xl"
  >
    <div class="flex items-center justify-between border-b border-[var(--studio-border)] px-4 py-2">
      <h3 class="text-sm font-medium">Exported definition</h3>
      <div class="flex gap-2">
        <button type="button" class={studio.btn} onclick={copyExport}>
          Copy
        </button>
        <button type="button" class={studio.btn} onclick={downloadExport}>
          Download
        </button>
        <button type="button" class={studio.btn} onclick={() => (showExport = false)}>
          Close
        </button>
      </div>
    </div>
    <pre class="overflow-auto p-4 text-xs text-[var(--studio-muted)]">{exportText}</pre>
  </div>
{/if}

<CatalogModal open={showCatalog} onClose={() => (showCatalog = false)} />