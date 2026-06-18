import type { StudioBootstrap } from "./types";

declare global {
  interface Window {
    __PALM_STUDIO__?: StudioBootstrap;
  }
}

const defaults: StudioBootstrap = {
  version: "dev",
  runtime: "ServerRuntime",
  apiBase: "/v1",
  explorer: "/explorer",
  studio: "/studio",
};

export const bootstrap: StudioBootstrap = {
  ...defaults,
  ...window.__PALM_STUDIO__,
};