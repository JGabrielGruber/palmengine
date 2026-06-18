<script lang="ts">
  import StudioLayout from "./components/layout/StudioLayout.svelte";
  import { bootstrap } from "./lib/bootstrap";
</script>

<StudioLayout version={bootstrap.version} />