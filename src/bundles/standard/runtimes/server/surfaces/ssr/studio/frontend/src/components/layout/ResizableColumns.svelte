<script lang="ts">
  import type { Snippet } from "svelte";

  type Props = {
    left: Snippet;
    center: Snippet;
    right: Snippet;
  };

  let { left, center, right }: Props = $props();

  const MIN = 200;
  const MAX = 480;
  const STORAGE_KEY = "palm-studio-panel-widths";
  const DEFAULT_LEFT = 260;
  const DEFAULT_RIGHT = 300;

  let leftWidth = $state(DEFAULT_LEFT);
  let rightWidth = $state(DEFAULT_RIGHT);
  let dragging: "left" | "right" | null = $state(null);
  let compact = $state(false);

  $effect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const saved = JSON.parse(raw) as { left?: number; right?: number };
      if (saved.left) {
        leftWidth = clamp(saved.left);
      }
      if (saved.right) {
        rightWidth = clamp(saved.right);
      }
    } catch {
      /* ignore */
    }
  });

  $effect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const update = () => {
      compact = media.matches;
    };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  });

  function clamp(value: number) {
    return Math.min(MAX, Math.max(MIN, value));
  }

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ left: leftWidth, right: rightWidth }),
    );
  }

  function onPointerMove(event: PointerEvent) {
    if (!dragging || compact) {
      return;
    }
    if (dragging === "left") {
      leftWidth = clamp(event.clientX);
    } else {
      rightWidth = clamp(window.innerWidth - event.clientX);
    }
  }

  function stopDragging() {
    if (!dragging) {
      return;
    }
    dragging = null;
    persist();
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", stopDragging);
  }

  function startDragging(side: "left" | "right", event: PointerEvent) {
    if (compact) {
      return;
    }
    dragging = side;
    event.preventDefault();
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", stopDragging);
  }
</script>

{#if compact}
  <div class="grid min-h-0 flex-1 grid-rows-[minmax(10rem,1fr)_minmax(0,2fr)]">
    <aside class="min-h-0 overflow-hidden border-b border-[var(--studio-border)] bg-[var(--studio-surface)]">
      {@render left()}
    </aside>
    <main class="relative min-h-0 overflow-hidden bg-[var(--studio-bg)]">
      {@render center()}
    </main>
  </div>
{:else}
  <div
    class="grid min-h-0 flex-1"
    style={`grid-template-columns: ${leftWidth}px 5px minmax(0, 1fr) 5px ${rightWidth}px;`}
  >
    <aside class="min-h-0 overflow-hidden bg-[var(--studio-surface)]">
      {@render left()}
    </aside>

    <button
      type="button"
      aria-label="Resize palette panel"
      class={`w-full cursor-col-resize border-x border-[var(--studio-border)] bg-[var(--studio-surface-2)] transition hover:bg-[var(--studio-surface)] ${dragging === "left" ? "bg-[var(--studio-surface)]" : ""}`}
      onpointerdown={(event) => startDragging("left", event)}
    ></button>

    <main class="relative min-h-0 overflow-hidden bg-[var(--studio-bg)]">
      {@render center()}
    </main>

    <button
      type="button"
      aria-label="Resize inspector panel"
      class={`w-full cursor-col-resize border-x border-[var(--studio-border)] bg-[var(--studio-surface-2)] transition hover:bg-[var(--studio-surface)] ${dragging === "right" ? "bg-[var(--studio-surface)]" : ""}`}
      onpointerdown={(event) => startDragging("right", event)}
    ></button>

    <aside class="min-h-0 overflow-hidden bg-[var(--studio-surface)]">
      {@render right()}
    </aside>
  </div>
{/if}