import { importFlowDefinition } from "./definition";
import type { ImportResult } from "./definition";
import type { ProcessDefinitionJson } from "../types";

export function importProcessDefinition(process: ProcessDefinitionJson): ImportResult {
  const flow = process.flows?.[0];
  if (!flow) {
    return {
      name: process.name,
      pattern: "wizard",
      nodes: [],
      edges: [],
    };
  }
  const imported = importFlowDefinition(flow);
  return {
    ...imported,
    name: process.name ?? imported.name,
  };
}