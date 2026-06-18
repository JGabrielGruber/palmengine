import type { PaletteItem, PaletteNodeKind, PaletteSection } from "../types";
import { studioEvents } from "./events";

export type StudioNodeTypeDef = {
  kind: PaletteNodeKind | string;
  label: string;
  description: string;
  icon?: string;
  draggable?: boolean;
  section?: string;
};

export type StudioPlugin = {
  id: string;
  name: string;
  version?: string;
  nodeTypes?: StudioNodeTypeDef[];
  paletteSections?: PaletteSection[];
  onInit?: () => void;
};

const plugins = new Map<string, StudioPlugin>();

function nodeTypeToPaletteItem(def: StudioNodeTypeDef, pluginId: string): PaletteItem {
  return {
    id: `${pluginId}:${def.kind}`,
    kind: def.kind as PaletteNodeKind,
    label: def.label,
    description: def.description,
    draggable: def.draggable ?? true,
  };
}

export const studioPlugins = {
  register(plugin: StudioPlugin) {
    plugins.set(plugin.id, plugin);
    plugin.onInit?.();
    studioEvents.emit("plugin:registered", { id: plugin.id, kind: "plugin" });
  },
  unregister(pluginId: string) {
    plugins.delete(pluginId);
  },
  all() {
    return [...plugins.values()];
  },
  extraPaletteSections(): PaletteSection[] {
    const sections: PaletteSection[] = [];
    for (const plugin of plugins.values()) {
      if (plugin.paletteSections?.length) {
        sections.push(...plugin.paletteSections);
      }
      if (plugin.nodeTypes?.length) {
        sections.push({
          id: `plugin:${plugin.id}`,
          label: plugin.name,
          items: plugin.nodeTypes.map((def) =>
            nodeTypeToPaletteItem(def, plugin.id),
          ),
        });
      }
    }
    return sections;
  },
  nodeTypeKinds(): string[] {
    const kinds = new Set<string>();
    for (const plugin of plugins.values()) {
      for (const def of plugin.nodeTypes ?? []) {
        kinds.add(def.kind);
      }
    }
    return [...kinds];
  },
};

studioPlugins.register({
  id: "palm-builtin",
  name: "Palm Built-ins",
  version: "1.0",
  nodeTypes: [
    {
      kind: "action",
      label: "Input Step",
      description: "Collect user input in a wizard step.",
      section: "structural",
    },
  ],
});