import { api } from "../shared/api/client";
import { createDraftSnapshot, loadLocalDraft, saveLocalDraft } from "../shared/draft/storage";
import type { StudioCanvas, StudioDraft } from "../shared/types";
import { canvasStore } from "./canvas.svelte";
import { projectStore } from "./project.svelte";

export const draftStore = {
  restoreLocal() {
    const draft = loadLocalDraft();
    if (!draft) {
      return false;
    }
    projectStore.setName(draft.name);
    projectStore.setPattern(draft.pattern);
    projectStore.setDraftId(draft.id);
    canvasStore.loadCanvas(draft.canvas);
    return true;
  },
  snapshot(): StudioDraft {
    const canvas: StudioCanvas = {
      nodes: canvasStore.nodes,
      edges: canvasStore.edges,
    };
    return createDraftSnapshot({
      id: projectStore.draftId,
      name: projectStore.name,
      pattern: projectStore.pattern,
      canvas,
    });
  },
  saveLocal() {
    const draft = draftStore.snapshot();
    saveLocalDraft(draft);
    projectStore.setDraftId(draft.id);
    projectStore.setDraftStatus("Saved locally");
    return draft;
  },
  async saveServer() {
    const local = draftStore.saveLocal();
    projectStore.setDraftStatus("Saving…");
    try {
      const response = await api.saveDraft({
        id: local.id,
        name: local.name,
        pattern: local.pattern,
        canvas: local.canvas,
        created_at: local.createdAt,
      });
      const draft = response.draft;
      projectStore.setDraftId(String(draft.id));
      projectStore.setDraftStatus("Saved to server");
      return draft;
    } catch (err) {
      projectStore.setDraftStatus(
        err instanceof Error ? err.message : "Server save failed",
      );
      throw err;
    }
  },
};