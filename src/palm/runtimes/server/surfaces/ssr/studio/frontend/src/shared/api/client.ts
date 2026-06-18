import { bootstrap } from "../bootstrap";

type RequestOptions = {
  method?: string;
  body?: unknown;
};

export class StudioApiClient {
  constructor(private readonly baseUrl: string = bootstrap.apiBase) {}

  async fetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: options.method ?? "GET",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API ${response.status}: ${path}`);
    }
    return (await response.json()) as T;
  }

  health() {
    return fetch("/health").then((response) => response.json());
  }
}

export const api = new StudioApiClient();