<script lang="ts">
  import FlowCanvas from "../canvas/FlowCanvas.svelte";
  import NodePalette from "../palette/NodePalette.svelte";
  import Inspector from "./Inspector.svelte";
  import Sidebar from "./Sidebar.svelte";
  import { bootstrap } from "../../lib/bootstrap";

  type Props = {
    version: string;
  };

  let { version }: Props = $props();
</script>

<div class="flex h-full min-h-0 flex-col bg-[#0b1220] text-[#e8edf7]">
  <header
    class="flex items-center justify-between border-b border-[#1e2a42] px-4 py-3"
  >
    <div class="flex items-center gap-3">
      <div
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1a2740] text-sm font-bold text-[#60a5fa]"
      >
        PS
      </div>
      <div>
        <h1 class="text-sm font-semibold tracking-wide">Palm Studio</h1>
        <p class="text-xs text-[#9aa8c7]">Visual flow builder</p>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs text-[#9aa8c7]">
      <a href={bootstrap.explorer} class="hover:text-[#e8edf7]">Explorer</a>
      <span class="rounded-full border border-[#2a3a5c] px-2 py-0.5">v{version}</span>
    </div>
  </header>

  <div class="grid min-h-0 flex-1 grid-cols-[16rem_1fr_18rem]">
    <Sidebar>
      <NodePalette />
    </Sidebar>
    <main class="relative min-h-0 border-x border-[#1e2a42]">
      <FlowCanvas />
    </main>
    <Inspector />
  </div>
</div>