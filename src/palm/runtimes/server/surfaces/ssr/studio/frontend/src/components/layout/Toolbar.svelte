<script lang="ts">
  import {
    exportFlowDefinition,
    exportProcessDefinition,
  } from "../../shared/export/definition";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { draftStore } from "../../stores/draft.svelte";
  import { projectStore } from "../../stores/project.svelte";

  let exportText = $state<string | null>(null);
  let showExport = $state(false);

  async function saveDraft(localOnly = false) {
    try {
      if (localOnly) {
        draftStore.saveLocal();
      } else {
        await draftStore.saveServer();
      }
    } catch {
      /* status surfaced via projectStore */
    }
  }

  function openExport(kind: "flow" | "process") {
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

  async function copyExport() {
    if (!exportText) {
      return;
    }
    await navigator.clipboard.writeText(exportText);
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

  <div class="ml-auto flex flex-wrap items-center gap-2">
    {#if projectStore.draftStatus}
      <span class="text-xs text-[#9aa8c7]">{projectStore.draftStatus}</span>
    {/if}
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