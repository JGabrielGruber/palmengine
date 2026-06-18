export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48) || "step";
}

export function nodeStepSlug(node: {
  label: string;
  ref?: string;
  meta?: Record<string, unknown>;
}): string {
  const fromMeta = node.meta?.slug;
  if (typeof fromMeta === "string" && fromMeta) {
    return fromMeta;
  }
  return slugify(node.ref ?? node.label);
}