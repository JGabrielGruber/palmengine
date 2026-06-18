<script lang="ts">
  import { feedbackStore } from "../../stores/feedback.svelte";

  const tone: Record<string, string> = {
    info: "border-[#2a3a5c] bg-[#151d2e] text-[#cbd5e1]",
    success: "border-[#14532d] bg-[#10251a] text-[#86efac]",
    warning: "border-[#713f12] bg-[#2a1f10] text-[#fcd34d]",
    error: "border-[#7f1d1d] bg-[#2a1010] text-[#fca5a5]",
  };
</script>

<div class="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
  {#each feedbackStore.messages as message (message.id)}
    <div
      class={`pointer-events-auto rounded-lg border px-3 py-2 text-sm shadow-lg ${tone[message.level]}`}
      role="status"
    >
      <div class="flex items-start justify-between gap-2">
        <span>{message.message}</span>
        <button
          type="button"
          class="text-xs opacity-70 hover:opacity-100"
          onclick={() => feedbackStore.dismiss(message.id)}
        >
          ✕
        </button>
      </div>
    </div>
  {/each}
</div>