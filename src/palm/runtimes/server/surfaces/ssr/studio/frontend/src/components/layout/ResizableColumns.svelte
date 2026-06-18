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
    if (!dragging) {
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
    dragging = side;
    event.preventDefault();
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", stopDragging);
  }
</script>

<div
  class="grid min-h-0 flex-1"
  style={`grid-template-columns: ${leftWidth}px 5px minmax(0, 1fr) 5px ${rightWidth}px;`}
>
  <aside class="min-h-0 overflow-hidden bg-[#0d1526]">
    {@render left()}
  </aside>

  <button
    type="button"
    aria-label="Resize palette panel"
    class={`w-full cursor-col-resize border-x border-[#1e2a42] bg-[#111a2c] transition hover:bg-[#1a2740] ${dragging === "left" ? "bg-[#1a2740]" : ""}`}
    onpointerdown={(event) => startDragging("left", event)}
  ></button>

  <main class="relative min-h-0 overflow-hidden bg-[#0b1220]">
    {@render center()}
  </main>

  <button
    type="button"
    aria-label="Resize inspector panel"
    class={`w-full cursor-col-resize border-x border-[#1e2a42] bg-[#111a2c] transition hover:bg-[#1a2740] ${dragging === "right" ? "bg-[#1a2740]" : ""}`}
    onpointerdown={(event) => startDragging("right", event)}
  ></button>

  <aside class="min-h-0 overflow-hidden bg-[#0d1526]">
    {@render right()}
  </aside>
</div>