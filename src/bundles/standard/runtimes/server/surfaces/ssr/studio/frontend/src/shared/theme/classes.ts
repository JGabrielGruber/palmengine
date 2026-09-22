/** Shared Tailwind class fragments using Explorer-aligned CSS variables. */

export const studio = {
  surface: "bg-[var(--studio-surface)]",
  surface2: "bg-[var(--studio-surface-2)]",
  border: "border-[var(--studio-border)]",
  text: "text-[var(--studio-text)]",
  muted: "text-[var(--studio-muted)]",
  accent: "text-[var(--studio-accent)]",
  btn:
    "rounded-md border border-[var(--studio-border)] px-3 py-1.5 text-xs transition hover:bg-[var(--studio-surface-2)]",
  btnAccent:
    "rounded-md bg-[var(--studio-accent-soft)] px-3 py-1.5 text-xs text-[var(--studio-bg)] hover:opacity-90",
  input:
    "rounded-md border border-[var(--studio-border)] bg-[var(--studio-surface)] px-2 py-1 text-sm text-[var(--studio-text)] outline-none focus:border-[var(--studio-accent)]",
};