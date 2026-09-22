import type { StudioCanvas, StudioDraft } from "../types";

const STORAGE_KEY = "palm-studio-draft";

export function loadLocalDraft(): StudioDraft | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StudioDraft;
  } catch {
    return null;
  }
}

export function saveLocalDraft(draft: StudioDraft): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
}

export function createDraftSnapshot(input: {
  id?: string;
  name: string;
  pattern: string;
  canvas: StudioCanvas;
  createdAt?: string;
}): StudioDraft {
  const now = new Date().toISOString();
  return {
    id: input.id ?? crypto.randomUUID(),
    name: input.name,
    pattern: input.pattern,
    canvas: input.canvas,
    updatedAt: now,
    createdAt: input.createdAt ?? now,
  };
}