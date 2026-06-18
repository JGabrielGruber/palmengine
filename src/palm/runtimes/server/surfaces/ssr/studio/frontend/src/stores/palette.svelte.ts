import { api } from "../shared/api/client";
import type { PaletteItem, PaletteSection } from "../shared/types";

let sections = $state<PaletteSection[]>([]);
let loading = $state(false);
let error = $state<string | null>(null);
let query = $state("");
let collapsed = $state<Record<string, boolean>>({});

function matches(item: PaletteItem, needle: string): boolean {
  const haystack = [
    item.label,
    item.description,
    item.ref ?? "",
    item.kind,
    item.provider ?? "",
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(needle);
}

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
  get query() {
    return query;
  },
  get filteredSections() {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return sections;
    }
    return sections
      .map((section) => ({
        ...section,
        items: section.items.filter((item) => matches(item, needle)),
      }))
      .filter((section) => section.items.length > 0);
  },
  isCollapsed(sectionId: string) {
    return collapsed[sectionId] ?? false;
  },
  setQuery(value: string) {
    query = value;
  },
  toggleSection(sectionId: string) {
    collapsed = {
      ...collapsed,
      [sectionId]: !paletteStore.isCollapsed(sectionId),
    };
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