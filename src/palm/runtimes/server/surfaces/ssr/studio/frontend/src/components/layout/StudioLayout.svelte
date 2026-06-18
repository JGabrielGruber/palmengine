<script lang="ts">
  import FlowCanvas from "../canvas/FlowCanvas.svelte";
  import OnboardingTour from "../onboarding/OnboardingTour.svelte";
  import SimulateModal from "../simulate/SimulateModal.svelte";
  import Inspector from "./Inspector.svelte";
  import ProjectTabs from "./ProjectTabs.svelte";
  import ResizableColumns from "./ResizableColumns.svelte";
  import SidebarPanel from "./SidebarPanel.svelte";
  import Toolbar from "./Toolbar.svelte";
  import ToastStack from "../feedback/ToastStack.svelte";
  import { bootstrap } from "../../shared/bootstrap";

  type Props = {
    version: string;
  };

  let { version }: Props = $props();
  let simulateOpen = $state(false);
  let inspectorOpen = $state(false);
</script>

<div
  class="relative flex h-full min-h-0 flex-col bg-[var(--studio-bg)] text-[var(--studio-text)]"
>
  <header
    class="flex shrink-0 items-center justify-between border-b border-[var(--studio-border)] px-4 py-3"
  >
    <div class="flex items-center gap-3">
      <div
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--studio-surface-2)] text-sm font-bold text-[var(--studio-accent)]"
      >
        PS
      </div>
      <div>
        <h1 class="text-sm font-semibold tracking-wide">Palm Studio</h1>
        <p class="text-xs text-[var(--studio-muted)]">Visual orchestrator</p>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs text-[var(--studio-muted)]">
      <a
        href={bootstrap.explorer}
        class="transition hover:text-[var(--studio-text)]"
      >
        Explorer
      </a>
      <span
        class="rounded-full border border-[var(--studio-border)] px-2 py-0.5"
      >
        v{version}
      </span>
    </div>
  </header>

  <ProjectTabs />

  <Toolbar onSimulate={() => (simulateOpen = true)} />

  <ToastStack />

  <ResizableColumns>
    {#snippet left()}
      <aside class="flex min-h-0 flex-col bg-[var(--studio-surface)]">
        <SidebarPanel />
      </aside>
    {/snippet}

    {#snippet center()}
      <FlowCanvas />
    {/snippet}

    {#snippet right()}
      <aside class="studio-hide-mobile flex min-h-0 flex-col">
        <Inspector />
      </aside>
    {/snippet}
  </ResizableColumns>

  <button
    type="button"
    class="studio-show-mobile fixed bottom-4 right-4 z-20 items-center gap-2 rounded-full border border-[var(--studio-border)] bg-[var(--studio-surface)] px-4 py-2 text-xs shadow-lg hover:bg-[var(--studio-surface-2)]"
    onclick={() => (inspectorOpen = true)}
    aria-label="Open inspector panel"
  >
    Inspector
  </button>

  {#if inspectorOpen}
    <div
      class="studio-show-mobile fixed inset-0 z-30 flex-col bg-black/50"
      role="presentation"
      onclick={() => (inspectorOpen = false)}
    >
      <div
        class="ml-auto flex h-full w-full max-w-sm flex-col border-l border-[var(--studio-border)] bg-[var(--studio-surface)] shadow-2xl"
        role="dialog"
        aria-label="Inspector"
        tabindex="-1"
        onclick={(event) => event.stopPropagation()}
        onkeydown={(event) => event.key === "Escape" && (inspectorOpen = false)}
      >
        <div class="flex justify-end border-b border-[var(--studio-border)] p-2">
          <button
            type="button"
            class="rounded px-2 py-1 text-sm hover:bg-[var(--studio-surface-2)]"
            onclick={() => (inspectorOpen = false)}
            aria-label="Close inspector"
          >
            ✕
          </button>
        </div>
        <Inspector />
      </div>
    </div>
  {/if}

  <SimulateModal open={simulateOpen} onClose={() => (simulateOpen = false)} />
  <OnboardingTour />
</div>