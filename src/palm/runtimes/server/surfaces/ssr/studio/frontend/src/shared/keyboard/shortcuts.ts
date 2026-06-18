export type Shortcut = {
  id: string;
  keys: string;
  description: string;
  handler: () => void;
  when?: () => boolean;
};

let registry: Shortcut[] = [];

export const shortcuts = {
  register(entry: Shortcut) {
    registry = [...registry.filter((item) => item.id !== entry.id), entry];
    return () => {
      registry = registry.filter((item) => item.id !== entry.id);
    };
  },
  all() {
    return registry;
  },
  handle(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    const typing =
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.tagName === "SELECT" ||
      target.isContentEditable;

    for (const entry of registry) {
      if (entry.when && !entry.when()) {
        continue;
      }
      if (!matches(event, entry.keys, typing)) {
        continue;
      }
      event.preventDefault();
      entry.handler();
      return true;
    }
    return false;
  },
};

function matches(event: KeyboardEvent, spec: string, typing: boolean): boolean {
  if (typing && !spec.includes("ctrl") && !spec.includes("meta")) {
    return false;
  }
  const parts = spec.toLowerCase().split("+");
  const key = parts[parts.length - 1];
  const needsCtrl = parts.includes("ctrl") || parts.includes("meta");
  const needsShift = parts.includes("shift");
  if (needsCtrl !== (event.ctrlKey || event.metaKey)) {
    return false;
  }
  if (needsShift !== event.shiftKey) {
    return false;
  }
  return event.key.toLowerCase() === key;
}