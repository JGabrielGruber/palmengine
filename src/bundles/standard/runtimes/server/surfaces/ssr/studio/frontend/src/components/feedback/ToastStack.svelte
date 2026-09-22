<script lang="ts">
  import { feedbackStore } from "../../stores/feedback.svelte";

  const tone: Record<string, string> = {
    info: "border-[var(--studio-border)] bg-[var(--studio-surface)] text-[var(--studio-text)]",
    success: "border-[var(--studio-accent)]/30 bg-[var(--studio-bg)] text-[var(--studio-accent)]",
    warning: "border-[var(--studio-amber)]/30 bg-[var(--studio-bg)] text-[var(--studio-amber)]",
    error: "border-[var(--studio-rose)]/30 bg-[var(--studio-bg)] text-[var(--studio-rose)]",
    loading: "border-[var(--studio-border)] bg-[var(--studio-surface)] text-[var(--studio-text)]",
  };
</script>

<div class="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
  {#each feedbackStore.messages as message (message.id)}
    <div
      class={`pointer-events-auto rounded-lg border px-3 py-2 text-sm shadow-lg ${tone[message.level]}`}
      role="status"
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          {#if message.level === "loading"}
            <div class="mb-1.5 h-1 overflow-hidden rounded-full bg-[var(--studio-surface-2)]">
              <div
                class="h-full rounded-full bg-[var(--studio-accent)] transition-all"
                style={`width:${message.progress ?? 35}%`}
              ></div>
            </div>
          {/if}
          <span>{message.message}</span>
        </div>
        {#if !message.sticky}
          <button
            type="button"
            class="text-xs opacity-70 hover:opacity-100"
            onclick={() => feedbackStore.dismiss(message.id)}
          >
            ✕
          </button>
        {/if}
      </div>
    </div>
  {/each}
</div>