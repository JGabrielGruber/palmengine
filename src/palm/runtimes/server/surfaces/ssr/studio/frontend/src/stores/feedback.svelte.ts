export type FeedbackLevel = "info" | "success" | "warning" | "error";

export type FeedbackMessage = {
  id: string;
  level: FeedbackLevel;
  message: string;
};

let messages = $state<FeedbackMessage[]>([]);

function push(level: FeedbackLevel, message: string) {
  const id = crypto.randomUUID();
  messages = [...messages, { id, level, message }];
  window.setTimeout(() => dismiss(id), 4500);
  return id;
}

function dismiss(id: string) {
  messages = messages.filter((entry) => entry.id !== id);
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
    return push("error", message);
  },
  dismiss,
};