import { api } from "../shared/api/client";
import { createDraftSnapshot, saveLocalDraft } from "../shared/draft/storage";
import type { StudioCanvas, StudioDraft } from "../shared/types";
import { canvasStore } from "./canvas.svelte";
import { feedbackStore } from "./feedback.svelte";
import { projectsStore } from "./projects.svelte";

export const draftStore = {
  restoreLocal() {
    return projectsStore.projects.length > 0;
  },
  snapshot(): StudioDraft {
    const active = projectsStore.active;
    const canvas: StudioCanvas = canvasStore.canvas;
    return createDraftSnapshot({
      id: active.id,
      name: active.name,
      pattern: active.pattern,
      canvas,
      createdAt: active.createdAt,
    });
  },
  saveLocal() {
    const version = projectsStore.bumpDraftVersion();
    const draft = draftStore.snapshot();
    saveLocalDraft(draft);
    feedbackStore.success(`Saved draft v${version}`);
    return draft;
  },
  async saveServer() {
    const local = draftStore.saveLocal();
    try {
      const response = await api.saveDraft({
        id: local.id,
        name: local.name,
        pattern: local.pattern,
        canvas: local.canvas,
        created_at: local.createdAt,
      });
      feedbackStore.success("Saved to server");
      return response.draft;
    } catch (err) {
      feedbackStore.error(
        err instanceof Error ? err.message : "Server save failed",
      );
      throw err;
    }
  },
};