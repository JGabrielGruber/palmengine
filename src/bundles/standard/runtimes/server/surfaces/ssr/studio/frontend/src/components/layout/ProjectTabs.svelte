<script lang="ts">
  import { projectsStore } from "../../stores/projects.svelte";
</script>

<div
  class="flex items-center gap-1 overflow-x-auto border-b border-[var(--studio-border)] bg-[var(--studio-surface)] px-2 py-1"
  role="tablist"
  aria-label="Open projects"
>
  {#each projectsStore.projects as project (project.id)}
    <div
      class={`group flex max-w-[12rem] shrink-0 items-center rounded-t-md border border-b-0 px-2 py-1 text-xs ${project.id === projectsStore.activeId ? "border-[var(--studio-accent)] bg-[var(--studio-bg)] text-[var(--studio-text)]" : "border-transparent text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
      role="tab"
      aria-selected={project.id === projectsStore.activeId}
    >
      <button
        type="button"
        class="truncate"
        onclick={() => projectsStore.switchTab(project.id)}
        title={`${project.name} · v${project.draftVersion}`}
      >
        {project.name}
        <span class="ml-1 opacity-60">v{project.draftVersion}</span>
      </button>
      {#if projectsStore.projects.length > 1}
        <button
          type="button"
          class="ml-1 rounded px-1 opacity-0 hover:bg-[var(--studio-surface-2)] group-hover:opacity-100"
          aria-label={`Close ${project.name}`}
          onclick={() => projectsStore.closeTab(project.id)}
        >
          ×
        </button>
      {/if}
    </div>
  {/each}
  <button
    type="button"
    class="shrink-0 rounded px-2 py-1 text-xs text-[var(--studio-accent)] hover:bg-[var(--studio-surface-2)]"
    onclick={() => projectsStore.newTab()}
    aria-label="New project tab"
  >
    +
  </button>
</div>