<script lang="ts">
  import { importFlowDefinition } from "../../shared/import/definition";
  import { api } from "../../shared/api/client";
  import { studio } from "../../shared/theme/classes";
  import type { StudioTemplateSummary } from "../../shared/types";
  import { feedbackStore } from "../../stores/feedback.svelte";
  import { projectsStore } from "../../stores/projects.svelte";

  let templates = $state<StudioTemplateSummary[]>([]);
  let categories = $state<string[]>([]);
  let category = $state("all");
  let loading = $state(false);
  let loadingId = $state<string | null>(null);

  const filtered = $derived(
    category === "all"
      ? templates
      : templates.filter((row) => row.category === category),
  );

  async function loadTemplates() {
    loading = true;
    try {
      const response = await api.listTemplates();
      templates = response.templates;
      categories = response.categories;
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to load templates",
      );
    } finally {
      loading = false;
    }
  }

  async function loadTemplate(templateId: string) {
    loadingId = templateId;
    try {
      const response = await api.getTemplate(templateId);
      const imported = importFlowDefinition(response.template.flow);
      projectsStore.openInNewTab({
        name: response.template.name,
        pattern: imported.pattern,
        canvas: {
          nodes: imported.nodes,
          edges: imported.edges,
          groups: [],
        },
      });
      feedbackStore.success(`Loaded template “${response.template.name}”`);
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Failed to load template",
      );
    } finally {
      loadingId = null;
    }
  }

  $effect(() => {
    void loadTemplates();
  });
</script>

<div class="space-y-3">
  <div class="flex flex-wrap gap-1">
    <button
      type="button"
      class={`rounded px-2 py-1 text-[11px] ${category === "all" ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
      onclick={() => (category = "all")}
    >
      All
    </button>
    {#each categories as row (row)}
      <button
        type="button"
        class={`rounded px-2 py-1 text-[11px] capitalize ${category === row ? "bg-[var(--studio-bg)] text-[var(--studio-accent)]" : "text-[var(--studio-muted)] hover:bg-[var(--studio-surface-2)]"}`}
        onclick={() => (category = row)}
      >
        {row.replace("-", " ")}
      </button>
    {/each}
  </div>

  {#if loading}
    <p class="text-xs text-[var(--studio-muted)]">Loading templates…</p>
  {:else if filtered.length === 0}
    <p class="text-xs text-[var(--studio-muted)]">No templates in this category.</p>
  {:else}
    <div class="space-y-2">
      {#each filtered as template (template.id)}
        <article class="rounded-lg border border-[var(--studio-border)] bg-[var(--studio-bg)] p-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <h4 class="truncate text-sm font-medium">{template.name}</h4>
              <p class="mt-1 text-[11px] leading-relaxed text-[var(--studio-muted)]">
                {template.description}
              </p>
              <div class="mt-2 flex flex-wrap gap-1">
                <span class="rounded-full border border-[var(--studio-border)] px-2 py-0.5 text-[10px] text-[var(--studio-muted)]">
                  {template.pattern}
                </span>
                {#each template.tags as tag (tag)}
                  <span class="rounded-full bg-[var(--studio-surface-2)] px-2 py-0.5 text-[10px] text-[var(--studio-muted)]">
                    {tag}
                  </span>
                {/each}
              </div>
            </div>
            <button
              type="button"
              class="{studio.btnAccent} shrink-0 disabled:opacity-50"
              disabled={loadingId === template.id}
              onclick={() => loadTemplate(template.id)}
            >
              {loadingId === template.id ? "…" : "Load"}
            </button>
          </div>
        </article>
      {/each}
    </div>
  {/if}
</div>