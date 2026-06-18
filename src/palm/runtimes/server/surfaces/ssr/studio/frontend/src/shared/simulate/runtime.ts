import type { FlowDefinitionJson, JobContext } from "../types";

export type SimulationState = {
  jobId: string | null;
  status: string;
  context: JobContext | null;
  error: string | null;
};

export async function submitFlowSimulation(
  apiBase: string,
  flow: FlowDefinitionJson,
): Promise<{ job_id: string; status: string }> {
  const response = await fetch(`${apiBase}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ flow }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      (payload as { message?: string }).message ??
        `Simulation failed (${response.status})`,
    );
  }
  return (await response.json()) as { job_id: string; status: string };
}

export async function fetchJobContext(
  apiBase: string,
  jobId: string,
): Promise<JobContext> {
  const response = await fetch(`${apiBase}/jobs/${encodeURIComponent(jobId)}/context`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to load job context (${response.status})`);
  }
  return (await response.json()) as JobContext;
}

export async function provideSimulationInput(
  apiBase: string,
  jobId: string,
  value: unknown,
): Promise<void> {
  const response = await fetch(`${apiBase}/jobs/${encodeURIComponent(jobId)}/input`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ value }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      (payload as { message?: string }).message ??
        `Input rejected (${response.status})`,
    );
  }
}

export function isTerminalStatus(status: string): boolean {
  return ["SUCCEEDED", "FAILED", "CANCELLED", "succeeded", "failed", "cancelled"].includes(
    status,
  );
}