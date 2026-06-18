export type FeedbackLevel = "info" | "success" | "warning" | "error" | "loading";

export type FeedbackMessage = {
  id: string;
  level: FeedbackLevel;
  message: string;
  progress?: number;
  sticky?: boolean;
};

let messages = $state<FeedbackMessage[]>([]);

function push(
  level: FeedbackLevel,
  message: string,
  options?: { progress?: number; sticky?: boolean; autoDismiss?: boolean },
) {
  const id = crypto.randomUUID();
  messages = [...messages, { id, level, message, ...options }];
  if (level !== "loading" && options?.autoDismiss !== false) {
    window.setTimeout(() => dismiss(id), level === "error" ? 7000 : 4500);
  }
  return id;
}

function dismiss(id: string) {
  messages = messages.filter((entry) => entry.id !== id);
}

function update(id: string, patch: Partial<FeedbackMessage>) {
  messages = messages.map((entry) =>
    entry.id === id ? { ...entry, ...patch } : entry,
  );
}

export const feedbackStore = {
  get messages() {
    return messages;
  },
  info(message: string) {
    return push("info", message);
  },
  success(message: string) {
    return push("success", message);
  },
  warning(message: string) {
    return push("warning", message);
  },
  error(message: string) {
    return push("error", message, { autoDismiss: true });
  },
  loading(message: string) {
    return push("loading", message, { sticky: true, autoDismiss: false });
  },
  progress(id: string, message: string, progress: number) {
    update(id, { message, progress, level: "loading" });
  },
  resolveLoading(id: string, message: string, level: FeedbackLevel = "success") {
    update(id, { message, level, progress: undefined, sticky: false });
    window.setTimeout(() => dismiss(id), 3500);
  },
  dismiss,
  async run<T>(
    label: string,
    task: () => Promise<T>,
    successMessage?: string,
  ): Promise<T> {
    const id = feedbackStore.loading(label);
    try {
      const result = await task();
      feedbackStore.resolveLoading(
        id,
        successMessage ?? `${label} complete`,
        "success",
      );
      return result;
    } catch (err) {
      feedbackStore.resolveLoading(
        id,
        err instanceof Error ? err.message : `${label} failed`,
        "error",
      );
      throw err;
    }
  },
};