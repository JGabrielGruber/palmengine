#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v4 - Flexible Step System with Random Workload
========================================================================
Beyond "vector of steps":
- Multiple independent, reusable step functions (not hardcoded in one pipeline)
- Random step selection / subset per tick (simulates branching Behavior Trees)
- Mask-based conditional execution on GPU (GPU-friendly)
- Persistent state + CUDA Graphs
- TTL support
"""

import argparse
import csv
import random
import time
from datetime import datetime
from typing import Callable, Dict, List

import numpy as np
import torch

# ============================================================
# STEP DEFINITIONS (Independent functions)
# ============================================================


def step_validate(
    data: torch.Tensor, state: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Step 1: Validation."""
    processed = data.clone()
    # Fixed: convert mask to boolean for torch.where
    bool_mask = mask > 0.5
    processed = torch.where(bool_mask.unsqueeze(1), processed * 0.95, processed * 0.0)
    return processed


def step_reserve(
    data: torch.Tensor, state: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Step 2: Reserve."""
    reserved = data * 0.85
    state_update = torch.mean(reserved, dim=1, keepdim=True) * 0.03
    state.add_(state_update * mask.unsqueeze(1).float())
    return reserved


def step_calculate(
    data: torch.Tensor, state: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Step 3: Calculate with state."""
    repeats = (data.shape[1] + state.shape[1] - 1) // state.shape[1]
    state_broadcast = state.repeat(1, repeats)[:, : data.shape[1]]
    calculated = data * 1.15 + torch.sin(state_broadcast)
    return calculated


def step_commit(
    data: torch.Tensor, state: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Step 4: Commit."""
    commit_value = data * 0.9
    state_update = torch.mean(commit_value, dim=1, keepdim=True) * 0.08
    state.add_(state_update * mask.unsqueeze(1).float())
    return commit_value


def step_ttl_cleanup(
    data: torch.Tensor,
    state: torch.Tensor,
    mask: torch.Tensor,
    timestamps: torch.Tensor,
    ttl: float,
    current_time: float,
) -> torch.Tensor:
    """Step 5: TTL cleanup."""
    expired = (current_time - timestamps) > ttl
    cleaned = torch.where(expired.unsqueeze(1), torch.zeros_like(data), data)
    timestamps[:] = torch.where(expired, current_time, timestamps)
    return cleaned


STEP_REGISTRY: Dict[str, Callable] = {
    "validate": step_validate,
    "reserve": step_reserve,
    "calculate": step_calculate,
    "commit": step_commit,
    "ttl_cleanup": step_ttl_cleanup,
}


class FlexibleGPUBackend:
    def __init__(
        self,
        batch_size: int = 1024,
        device: str = "cuda",
        enable_ttl: bool = True,
        random_steps: bool = True,
    ):
        self.device = device
        self.batch_size = batch_size
        self.enable_ttl = enable_ttl
        self.random_steps = random_steps

        self.data_dim = 64
        self.state_dim = 32

        self.input_buf = torch.zeros(
            (batch_size, self.data_dim), device=device, dtype=torch.float32
        )
        self.state_buf = torch.zeros(
            (batch_size, self.state_dim), device=device, dtype=torch.float32
        )
        self.output_buf = torch.zeros(
            (batch_size, self.data_dim), device=device, dtype=torch.float32
        )

        if enable_ttl:
            self.timestamp_buf = torch.zeros(
                batch_size, device=device, dtype=torch.float32
            )
            self.ttl = 5.0

        self.graph = None
        self.available_steps = list(STEP_REGISTRY.keys())
        self._capture_graph()

    def _capture_graph(self):
        if self.device != "cuda" or not torch.cuda.is_available():
            print("Warning: CUDA not available. Using eager mode.")
            return

        dummy = torch.randn(self.batch_size, self.data_dim, device=self.device)
        self.process_tick(dummy, step_names=self.available_steps[:3])

        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._execute_steps(
                self.input_buf,
                self.state_buf,
                self.output_buf,
                step_names=self.available_steps[:3],
                random_mask=False,
            )
        self.graph = g

    def _execute_steps(
        self,
        inputs: torch.Tensor,
        state: torch.Tensor,
        outputs: torch.Tensor,
        step_names: List[str],
        random_mask: bool = True,
    ):
        current_time = time.time()
        current = inputs.clone()

        for step_name in step_names:
            if step_name not in STEP_REGISTRY:
                continue
            step_fn = STEP_REGISTRY[step_name]

            if random_mask:
                mask = (torch.rand(self.batch_size, device=self.device) > 0.3).float()
            else:
                mask = torch.ones(self.batch_size, device=self.device)

            if step_name == "ttl_cleanup" and self.enable_ttl:
                current = step_fn(
                    current, state, mask, self.timestamp_buf, self.ttl, current_time
                )
            else:
                current = step_fn(current, state, mask)

        outputs.copy_(current)

    def process_tick(
        self, new_inputs: torch.Tensor, step_names: List[str] = None
    ) -> torch.Tensor:
        if step_names is None:
            if self.random_steps:
                num_steps = random.randint(2, min(4, len(self.available_steps)))
                step_names = random.sample(self.available_steps, num_steps)
            else:
                step_names = self.available_steps[:3]

        if self.graph is not None and len(step_names) == 3:
            self.input_buf.copy_(new_inputs)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            self.input_buf.copy_(new_inputs)
            self._execute_steps(
                self.input_buf,
                self.state_buf,
                self.output_buf,
                step_names=step_names,
                random_mask=self.random_steps,
            )
            return self.output_buf.clone()

    def get_vram_usage(self) -> float:
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated(self.device) / (1024**2)
        return 0.0


def run_v4_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 200,
    enable_ttl: bool = True,
    random_steps: bool = True,
    export_csv: str = None,
):
    print("Palm GPU Prototype v4 - Flexible Steps + Random Workload")
    print("=" * 65)
    print(f"Batch sizes: {batch_sizes}")
    print(f"Ticks: {num_ticks} | Random Steps: {random_steps} | TTL: {enable_ttl}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # CPU baseline (simplified)
        cpu_start = time.perf_counter()
        data = np.random.randn(bs, 64).astype(np.float32)
        state = np.zeros((bs, 32), dtype=np.float32)

        for _ in range(num_ticks):
            steps_to_run = random.sample(
                list(STEP_REGISTRY.keys()), random.randint(2, 4)
            )
            for step_name in steps_to_run:
                if step_name in ["validate", "reserve", "calculate", "commit"]:
                    repeats = (64 + 31) // 32
                    state_broadcast = np.repeat(state, repeats, axis=1)[:, :64]
                    data = data * 0.9 + np.sin(state_broadcast) * 0.1

        cpu_time = time.perf_counter() - cpu_start
        cpu_throughput = (bs * num_ticks) / cpu_time
        print(f"CPU  | {cpu_time:.4f}s | {cpu_throughput:10.0f} items/s (simplified)")

        # GPU
        gpu_time = 0.0
        gpu_throughput = 0.0
        vram_mb = 0.0

        if torch.cuda.is_available():
            backend = FlexibleGPUBackend(
                batch_size=bs, enable_ttl=enable_ttl, random_steps=random_steps
            )
            inputs = torch.randn(bs, 64, device="cuda")

            backend.process_tick(inputs)  # warmup

            gpu_start = time.perf_counter()
            for _ in range(num_ticks):
                inputs = torch.randn(bs, 64, device="cuda")
                _ = backend.process_tick(inputs)
            torch.cuda.synchronize()
            gpu_time = time.perf_counter() - gpu_start
            gpu_throughput = (bs * num_ticks) / gpu_time
            vram_mb = backend.get_vram_usage()

            print(
                f"GPU  | {gpu_time:.4f}s | {gpu_throughput:10.0f} items/s | VRAM: {vram_mb:.1f} MB"
            )
        else:
            print("GPU  | CUDA not available — skipped")

        speedup = gpu_throughput / cpu_throughput if gpu_throughput > 0 else 0.0

        results.append(
            {
                "batch_size": bs,
                "cpu_time": round(cpu_time, 4),
                "cpu_throughput": round(cpu_throughput),
                "gpu_time": round(gpu_time, 4),
                "gpu_throughput": round(gpu_throughput),
                "speedup": round(speedup, 1),
                "vram_mb": round(vram_mb, 1),
                "random_steps": random_steps,
                "ttl": enable_ttl,
                "timestamp": datetime.now().isoformat(),
            }
        )

    print("\n" + "=" * 70)
    print("SUMMARY - Palm GPU v4 (Flexible Random Steps)")
    print("=" * 70)
    for r in results:
        print(
            f"Batch {r['batch_size']:5d} | CPU: {r['cpu_throughput']:9d} | GPU: {r['gpu_throughput']:9d} | "
            f"Speedup: {r['speedup']:5.1f}x | VRAM: {r['vram_mb']:5.1f}MB"
        )

    if export_csv:
        with open(export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults exported to {export_csv}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Palm Engine GPU Prototype v4")
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[64, 256, 1024, 4096, 8192]
    )
    parser.add_argument("--ticks", type=int, default=200)
    parser.add_argument("--ttl", action="store_true", default=True)
    parser.add_argument("--random-steps", action="store_true", default=True)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v4_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        enable_ttl=args.ttl,
        random_steps=args.random_steps,
        export_csv=args.export_csv,
    )


if __name__ == "__main__":
    main()
