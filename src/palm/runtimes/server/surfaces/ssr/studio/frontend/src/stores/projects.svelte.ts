import { studioEvents } from "../shared/extensions/events";
import type { StudioCanvas, StudioProject } from "../shared/types";

const STORAGE_KEY = "palm-studio-projects";

function now() {
  return new Date().toISOString();
}

function emptyCanvas(): StudioCanvas {
  return { nodes: [], edges: [], groups: [] };
}

function newProject(name?: string): StudioProject {
  const timestamp = now();
  return {
    id: crypto.randomUUID(),
    name: name ?? `flow-${Math.floor(Math.random() * 900 + 100)}`,
    pattern: "wizard",
    canvas: emptyCanvas(),
    draftVersion: 1,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
}

let projects = $state<StudioProject[]>([newProject("studio-flow")]);
let activeId = $state(projects[0].id);

function persist() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ activeId, projects }),
  );
}

function loadPersisted() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return false;
  }
  try {
    const saved = JSON.parse(raw) as {
      activeId?: string;
      projects?: StudioProject[];
    };
    if (saved.projects?.length) {
      projects = saved.projects;
      activeId = saved.activeId ?? saved.projects[0].id;
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

loadPersisted();

export const projectsStore = {
  get projects() {
    return projects;
  },
  get activeId() {
    return activeId;
  },
  get active(): StudioProject {
    return projects.find((project) => project.id === activeId) ?? projects[0];
  },
  get activeIndex() {
    return projects.findIndex((project) => project.id === activeId);
  },
  switchTab(projectId: string) {
    if (!projects.some((project) => project.id === projectId)) {
      return;
    }
    activeId = projectId;
    persist();
    studioEvents.emit("project:switched", { projectId });
  },
  newTab() {
    const project = newProject();
    projects = [...projects, project];
    activeId = project.id;
    persist();
    studioEvents.emit("project:switched", { projectId: project.id });
    return project;
  },
  closeTab(projectId: string) {
    if (projects.length <= 1) {
      return;
    }
    const index = projects.findIndex((project) => project.id === projectId);
    if (index < 0) {
      return;
    }
    projects = projects.filter((project) => project.id !== projectId);
    if (activeId === projectId) {
      const next = projects[Math.max(0, index - 1)];
      activeId = next.id;
      studioEvents.emit("project:switched", { projectId: next.id });
    }
    persist();
  },
  renameActive(name: string) {
    projectsStore.updateActive({ name: name.trim() || projectsStore.active.name });
  },
  setPattern(pattern: string) {
    projectsStore.updateActive({ pattern });
  },
  updateActiveCanvas(canvas: StudioCanvas) {
    projectsStore.updateActive({ canvas });
  },
  updateActive(patch: Partial<Pick<StudioProject, "name" | "pattern" | "canvas">>) {
    const timestamp = now();
    projects = projects.map((project) =>
      project.id === activeId
        ? { ...project, ...patch, updatedAt: timestamp }
        : project,
    );
    persist();
  },
  bumpDraftVersion() {
    const current = projectsStore.active;
    const version = current.draftVersion + 1;
    projectsStore.updateActive({ draftVersion: version });
    persist();
    studioEvents.emit("project:saved", {
      projectId: current.id,
      version,
    });
    return version;
  },
  replaceActive(project: Partial<StudioProject>) {
    projects = projects.map((entry) =>
      entry.id === activeId ? { ...entry, ...project, updatedAt: now() } : entry,
    );
    persist();
  },
};

/** Backward-compatible accessors used across the UI. */
export const projectStore = {
  get name() {
    return projectsStore.active.name;
  },
  get pattern() {
    return projectsStore.active.pattern;
  },
  get draftId() {
    return projectsStore.active.id;
  },
  get draftVersion() {
    return projectsStore.active.draftVersion;
  },
  get draftStatus() {
    return null as string | null;
  },
  setName(value: string) {
    projectsStore.renameActive(value);
  },
  setPattern(value: string) {
    projectsStore.setPattern(value);
  },
  setDraftId(_value: string | undefined) {
    /* tab id is project id */
  },
  setDraftStatus(_value: string | null) {
    /* use feedbackStore */
  },
};