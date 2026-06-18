import { api } from "../shared/api/client";
import type { PaletteItem, PaletteSection } from "../shared/types";

let sections = $state<PaletteSection[]>([]);
let loading = $state(false);
let error = $state<string | null>(null);

export const paletteStore = {
  get sections() {
    return sections;
  },
  get loading() {
    return loading;
  },
  get error() {
    return error;
  },
  get draggableItems() {
    return sections.flatMap((section) =>
      section.items.filter((item) => item.draggable),
    );
  },
  async load() {
    loading = true;
    error = null;
    try {
      const payload = await api.palette();
      sections = payload.sections;
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load palette";
      sections = [];
    } finally {
      loading = false;
    }
  },
  findItem(id: string): PaletteItem | undefined {
    for (const section of sections) {
      const item = section.items.find((entry) => entry.id === id);
      if (item) {
        return item;
      }
    }
    return undefined;
  },
};