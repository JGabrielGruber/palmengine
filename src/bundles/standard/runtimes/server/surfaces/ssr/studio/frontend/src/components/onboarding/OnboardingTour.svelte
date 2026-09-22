<script lang="ts">
  const STORAGE_KEY = "palm-studio-onboarded";

  type Step = {
    title: string;
    body: string;
    target?: string;
  };

  const steps: Step[] = [
    {
      title: "Welcome to Palm Studio",
      body: "Build flows visually, simulate them live, and save definitions to the Palm catalog.",
    },
    {
      title: "Drag from the palette",
      body: "Open the Palette tab, drag nodes onto the canvas, and connect them with handles.",
      target: "palette",
    },
    {
      title: "Try a template",
      body: "Switch to Templates for curated examples — one click loads a ready-made flow.",
      target: "templates",
    },
    {
      title: "Simulate & save",
      body: "Use Simulate to preview wizard steps, then Save as Flow to register in the repository.",
      target: "toolbar",
    },
  ];

  let open = $state(false);
  let index = $state(0);

  $effect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      open = true;
    }
  });

  function close(persist = true) {
    open = false;
    if (persist) {
      localStorage.setItem(STORAGE_KEY, "1");
    }
  }

  function next() {
    if (index >= steps.length - 1) {
      close(true);
      index = 0;
      return;
    }
    index += 1;
  }

  export function restart() {
    index = 0;
    open = true;
  }
</script>

{#if open}
  <div
    class="absolute inset-0 z-40 flex items-end justify-center bg-black/50 p-4 sm:items-center"
    role="dialog"
    aria-modal="true"
    aria-label="Studio onboarding"
  >
    <div
      class="w-full max-w-md rounded-xl border border-[var(--studio-border)] bg-[var(--studio-surface)] p-4 shadow-2xl"
    >
      <p class="text-[10px] uppercase tracking-wider text-[var(--studio-muted)]">
        Step {index + 1} of {steps.length}
      </p>
      <h3 class="mt-1 text-base font-semibold">{steps[index].title}</h3>
      <p class="mt-2 text-sm text-[var(--studio-muted)]">{steps[index].body}</p>
      <div class="mt-4 flex items-center justify-between gap-2">
        <button
          type="button"
          class="text-xs text-[var(--studio-muted)] hover:text-[var(--studio-text)]"
          onclick={() => close(true)}
        >
          Skip tour
        </button>
        <div class="flex gap-2">
          {#if index > 0}
            <button
              type="button"
              class="rounded border border-[var(--studio-border)] px-3 py-1.5 text-xs hover:bg-[var(--studio-surface-2)]"
              onclick={() => (index -= 1)}
            >
              Back
            </button>
          {/if}
          <button
            type="button"
            class="rounded bg-[var(--studio-accent-soft)] px-3 py-1.5 text-xs text-[var(--studio-bg)]"
            onclick={next}
          >
            {index >= steps.length - 1 ? "Get started" : "Next"}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}