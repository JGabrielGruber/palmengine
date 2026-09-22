<script lang="ts">
  import { exportFlowDefinition } from "../../shared/export/definition";
  import { bootstrap } from "../../shared/bootstrap";
  import {
    fetchJobContext,
    isTerminalStatus,
    provideSimulationInput,
    submitFlowSimulation,
  } from "../../shared/simulate/runtime";
  import { studioEvents } from "../../shared/extensions/events";
  import { studio } from "../../shared/theme/classes";
  import { canvasStore } from "../../stores/canvas.svelte";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { projectsStore } from "../../stores/projects.svelte";
  import { simulationStore } from "../../stores/simulation.svelte";
  import { validationStore } from "../../stores/validation.svelte";
  import type { JobContext } from "../../shared/types";

  type Props = {
    open: boolean;
    onClose: () => void;
  };

  let { open, onClose }: Props = $props();

  let loading = $state(false);
  let jobId = $state<string | null>(null);
  let context = $state<JobContext | null>(null);
  let inputValue = $state("");
  let pollTimer: ReturnType<typeof setInterval> | undefined;

  const prompt = $derived(context?.pattern?.prompt ?? "Waiting for runtime…");
  const status = $derived(context?.status ?? "idle");
  const validationError = $derived(context?.pattern?.validation_error);
  const fieldType = $derived(context?.pattern?.field_type ?? "text");
  const choices = $derived(context?.pattern?.choices ?? []);
  const waitingForInput = $derived(
    status === "WAITING_FOR_INPUT" || status === "waiting_for_input",
  );
  const trace = $derived(simulationStore.trace);

  async function refreshContext(id: string) {
    context = await fetchJobContext(bootstrap.apiBase, id);
    simulationStore.updateContext(context);
    if (isTerminalStatus(context.status)) {
      stopPolling();
      studioEvents.emit("simulate:completed", {
        jobId: id,
        status: context.status,
      });
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = undefined;
    }
  }

  async function startSimulation() {
    if (validationStore.errorCount > 0) {
      feedbackStore.warning("Fix validation errors before simulating.");
      return;
    }
    loading = true;
    jobId = null;
    context = null;
    try {
      const flow = exportFlowDefinition({
        name: projectsStore.active.name,
        pattern: projectsStore.active.pattern,
        nodes: canvasStore.nodes,
        edges: canvasStore.edges,
      });
      const accepted = await submitFlowSimulation(bootstrap.apiBase, flow);
      jobId = accepted.job_id;
      simulationStore.start(accepted.job_id);
      studioEvents.emit("simulate:started", { jobId: accepted.job_id });
      await refreshContext(accepted.job_id);
      pollTimer = setInterval(() => {
        if (jobId) {
          void refreshContext(jobId);
        }
      }, 1000);
      feedbackStore.success("Simulation started — watch the canvas for live trace");
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Simulation failed",
      );
    } finally {
      loading = false;
    }
  }

  async function submitInput() {
    if (!jobId) {
      return;
    }
    loading = true;
    try {
      const raw = inputValue.trim();
      const value = Number.isNaN(Number(raw)) ? raw : Number(raw);
      await provideSimulationInput(bootstrap.apiBase, jobId, value);
      inputValue = "";
      await refreshContext(jobId);
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to submit input",
      );
    } finally {
      loading = false;
    }
  }

  function close() {
    stopPolling();
    jobId = null;
    context = null;
    simulationStore.stop();
    onClose();
  }

  $effect(() => {
    if (!open) {
      stopPolling();
      if (!simulationStore.active) {
        return;
      }
    }
    return () => {
      if (!open) {
        simulationStore.stop();
      }
      stopPolling();
    };
  });
</script>

{#if open}
  <div
    class="absolute inset-0 z-30 flex items-center justify-center bg-black/60 p-4"
    role="dialog"
    aria-modal="true"
    aria-label="Flow simulation"
  >
    <div
      class="flex max-h-[85%] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-[var(--studio-border)] bg-[var(--studio-surface)] shadow-2xl"
    >
      <div class="flex items-center justify-between border-b border-[var(--studio-border)] px-4 py-3">
        <div>
          <h3 class="text-sm font-semibold">Simulate flow</h3>
          <p class="text-xs text-[var(--studio-muted)]">
            Live preview — active steps highlight on the canvas
          </p>
        </div>
        <button
          type="button"
          class="rounded px-2 py-1 text-sm hover:bg-[var(--studio-surface-2)]"
          onclick={close}
        >
          ✕
        </button>
      </div>

      <div class="space-y-4 overflow-y-auto p-4 text-sm">
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="rounded-full border border-[var(--studio-border)] px-2 py-0.5">
            {status}
          </span>
          {#if trace.activeStep}
            <span class="font-mono text-[var(--studio-accent)]">
              step: {trace.activeStep}
            </span>
          {/if}
          {#if jobId}
            <span class="font-mono text-[var(--studio-muted)]">{jobId}</span>
          {/if}
        </div>

        {#if !jobId}
          <button
            type="button"
            class="{studio.btnAccent} w-full disabled:opacity-50"
            disabled={loading}
            onclick={startSimulation}
          >
            {loading ? "Starting…" : "Start simulation"}
          </button>
        {:else if context}
          <section class="rounded-lg border border-[var(--studio-border)] bg-[var(--studio-bg)] p-3">
            <h4 class="text-xs uppercase tracking-wide text-[var(--studio-muted)]">
              Current step
            </h4>
            <p class="mt-2">{prompt}</p>
            {#if context.pattern?.step}
              <p class="mt-1 font-mono text-xs text-[var(--studio-muted)]">
                slug: {context.pattern.step}
              </p>
            {/if}
            {#if validationError}
              <p class="mt-2 text-xs text-[var(--studio-rose)]">{validationError}</p>
            {/if}
          </section>

          {#if waitingForInput}
            <div class="space-y-2">
              <label class="text-xs text-[var(--studio-muted)]" for="sim-input">
                Your input
              </label>
              {#if choices.length > 0}
                <select
                  id="sim-input"
                  class="{studio.input} w-full py-2"
                  bind:value={inputValue}
                >
                  <option value="">Select…</option>
                  {#each choices as choice (choice)}
                    <option value={choice}>{choice}</option>
                  {/each}
                </select>
              {:else if fieldType === "number"}
                <input
                  id="sim-input"
                  type="number"
                  class="{studio.input} w-full"
                  bind:value={inputValue}
                  onkeydown={(event) => event.key === "Enter" && submitInput()}
                />
              {:else}
                <input
                  id="sim-input"
                  class="{studio.input} w-full"
                  bind:value={inputValue}
                  onkeydown={(event) => event.key === "Enter" && submitInput()}
                />
              {/if}
              <button
                type="button"
                class="{studio.btnAccent} w-full disabled:opacity-50"
                disabled={loading || !inputValue.trim()}
                onclick={submitInput}
              >
                Submit input
              </button>
            </div>
          {/if}

          {#if trace.completedNodeIds.length > 0}
            <p class="text-xs text-[var(--studio-muted)]">
              {trace.completedNodeIds.length} step(s) completed on canvas
            </p>
          {/if}

          {#if context.result}
            <pre class="overflow-auto rounded-lg bg-[var(--studio-bg)] p-3 text-xs">{JSON.stringify(context.result, null, 2)}</pre>
          {/if}
          {#if context.error}
            <p class="text-sm text-[var(--studio-rose)]">{context.error}</p>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}