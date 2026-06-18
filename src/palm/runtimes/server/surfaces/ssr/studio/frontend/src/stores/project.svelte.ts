let name = $state("studio-flow");
let pattern = $state("wizard");
let draftId = $state<string | undefined>(undefined);
let draftStatus = $state<string | null>(null);

export const projectStore = {
  get name() {
    return name;
  },
  get pattern() {
    return pattern;
  },
  get draftId() {
    return draftId;
  },
  get draftStatus() {
    return draftStatus;
  },
  setName(value: string) {
    name = value.trim() || "studio-flow";
  },
  setPattern(value: string) {
    pattern = value;
  },
  setDraftId(value: string | undefined) {
    draftId = value;
  },
  setDraftStatus(value: string | null) {
    draftStatus = value;
  },
};