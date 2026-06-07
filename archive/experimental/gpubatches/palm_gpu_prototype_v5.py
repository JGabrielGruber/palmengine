#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v5 - Per-Instance Step Control (GPU Dispatch)
========================================================================
Major architectural improvement:

- CPU mainly feeds **input data** into fixed VRAM buffers.
- Each workflow instance has its own **step_index** (program counter) stored in VRAM.
- GPU handles **step dispatching internally** based on per-instance step_index.
- Much better CUDA Graph compatibility and lower CPU overhead.
- Still supports random workload simulation.
"""

import argparse
import csv
import random
import time
from datetime import datetime
from typing import Callable, List

import numpy as np
import torch

# ============================================================
# INDEPENDENT STEP FUNCTIONS
# ============================================================


def step_validate(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    """Step 0: Validation"""
    return data * 0.98


def step_reserve(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    """Step 1: Reserve / allocation"""
    reserved = data * 0.82
    state_update = torch.mean(reserved, dim=1, keepdim=True) * 0.04
    state.add_(state_update)
    return reserved


def step_calculate(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    """Step 2: Calculation with state"""
    repeats = (data.shape[1] + state.shape[1] - 1) // state.shape[1]
    state_broadcast = state.repeat(1, repeats)[:, : data.shape[1]]
    return data * 1.12 + torch.sin(state_broadcast)


def step_commit(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    """Step 3: Commit / final update"""
    commit_val = data * 0.95
    state_update = torch.mean(commit_val, dim=1, keepdim=True) * 0.07
    state.add_(state_update)
    return commit_val


def step_ttl_cleanup(
    data: torch.Tensor,
    state: torch.Tensor,
    timestamps: torch.Tensor,
    ttl: float,
    current_time: float,
) -> torch.Tensor:
    """Step 4: TTL eviction"""
    expired = (current_time - timestamps) > ttl
    cleaned = torch.where(expired.unsqueeze(1), torch.zeros_like(data), data)
    timestamps[:] = torch.where(expired, current_time, timestamps)
    return cleaned


STEP_FUNCS: List[Callable] = [
    step_validate,
    step_reserve,
    step_calculate,
    step_commit,
    step_ttl_cleanup,
]

NUM_STEPS = len(STEP_FUNCS)


class PalmGPUBackendV5:
    """
    GPU backend with per-instance step control.
    CPU feeds data + occasionally updates step indices.
    GPU does the actual step dispatching.
    """

    def __init__(
        self,
        batch_size: int = 1024,
        device: str = "cuda",
        enable_ttl: bool = True,
        random_progression: bool = True,
    ):
        self.device = device
        self.batch_size = batch_size
        self.enable_ttl = enable_ttl
        self.random_progression = random_progression

        self.data_dim = 64
        self.state_dim = 32

        # Persistent VRAM buffers
        self.input_buf = torch.zeros(
            (batch_size, self.data_dim), device=device, dtype=torch.float32
        )
        self.state_buf = torch.zeros(
            (batch_size, self.state_dim), device=device, dtype=torch.float32
        )
        self.output_buf = torch.zeros(
            (batch_size, self.data_dim), device=device, dtype=torch.float32
        )
        self.step_index_buf = torch.zeros(
            batch_size, device=device, dtype=torch.long
        )  # Per-instance step counter

        if enable_ttl:
            self.timestamp_buf = torch.zeros(
                batch_size, device=device, dtype=torch.float32
            )
            self.ttl = 5.0

        self.graph = None
        self._capture_graph()

    def _capture_graph(self):
        if self.device != "cuda" or not torch.cuda.is_available():
            print("Warning: CUDA not available. Using eager mode.")
            return

        dummy = torch.randn(self.batch_size, self.data_dim, device=self.device)
        self.process_tick(dummy)

        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._gpu_tick(self.input_buf, self.state_buf, self.output_buf)
        self.graph = g

    def _gpu_tick(
        self, inputs: torch.Tensor, state: torch.Tensor, outputs: torch.Tensor
    ):
        """Single GPU tick that dispatches based on per-instance step_index."""
        current_time = time.time()
        current = inputs.clone()

        # Dispatch each possible step using masks (GPU-friendly)
        for step_idx in range(NUM_STEPS):
            mask = self.step_index_buf == step_idx

            if step_idx == 4 and self.enable_ttl:  # TTL step
                temp = STEP_FUNCS[step_idx](
                    current, state, self.timestamp_buf, self.ttl, current_time
                )
            else:
                temp = STEP_FUNCS[step_idx](current, state)

            # Apply only to instances at this step
            current = torch.where(mask.unsqueeze(1), temp, current)

        outputs.copy_(current)

        # Advance step indices (GPU side)
        if self.random_progression:
            advance_mask = torch.rand(self.batch_size, device=self.device) > 0.4
            self.step_index_buf.add_(advance_mask.long())
            self.step_index_buf %= NUM_STEPS
        else:
            self.step_index_buf.add_(1)
            self.step_index_buf %= NUM_STEPS

    def process_tick(self, new_inputs: torch.Tensor) -> torch.Tensor:
        """Main entry point. CPU feeds data, GPU does the work."""
        if self.graph is not None:
            self.input_buf.copy_(new_inputs)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            self.input_buf.copy_(new_inputs)
            self._gpu_tick(self.input_buf, self.state_buf, self.output_buf)
            return self.output_buf.clone()

    def get_vram_usage(self) -> float:
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated(self.device) / (1024**2)
        return 0.0


def run_v5_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 200,
    enable_ttl: bool = True,
    random_progression: bool = True,
    export_csv: str = None,
):
    print("Palm GPU Prototype v5 - Per-Instance Step Control (GPU Dispatch)")
    print("=" * 70)
    print(f"Batch sizes: {batch_sizes}")
    print(
        f"Ticks: {num_ticks} | Random Progression: {random_progression} | TTL: {enable_ttl}"
    )
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # === CPU baseline (fixed broadcasting) ===
        cpu_start = time.perf_counter()
        data = np.random.randn(bs, 64).astype(np.float32)
        state = np.zeros((bs, 32), dtype=np.float32)
        step_idx = np.zeros(bs, dtype=np.int32)

        for _ in range(num_ticks):
            for i in range(bs):
                s = step_idx[i] % NUM_STEPS
                if s < 4:  # Skip TTL in simplified CPU for speed
                    # Fixed broadcasting
                    repeats = (64 + 31) // 32
                    state_broadcast = np.repeat(state[i : i + 1], repeats, axis=1)[
                        :, :64
                    ]
                    data[i] = data[i] * 0.9 + np.sin(state_broadcast[0]) * 0.1
                step_idx[i] = (step_idx[i] + 1) % NUM_STEPS

        cpu_time = time.perf_counter() - cpu_start
        cpu_throughput = (bs * num_ticks) / cpu_time
        print(
            f"CPU  | {cpu_time:.4f}s | {cpu_throughput:10.0f} items/s (simplified per-instance)"
        )

        # === GPU ===
        gpu_time = 0.0
        gpu_throughput = 0.0
        vram_mb = 0.0

        if torch.cuda.is_available():
            backend = PalmGPUBackendV5(
                batch_size=bs,
                enable_ttl=enable_ttl,
                random_progression=random_progression,
            )
            inputs = torch.randn(bs, 64, device="cuda")

            backend.process_tick(inputs)  # warmup + capture

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
                "random_progression": random_progression,
                "ttl": enable_ttl,
                "timestamp": datetime.now().isoformat(),
            }
        )

    print("\n" + "=" * 75)
    print("SUMMARY - Palm GPU v5 (Per-Instance Step Control)")
    print("=" * 75)
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
    parser = argparse.ArgumentParser(description="Palm Engine GPU Prototype v5")
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[64, 256, 1024, 4096, 8192]
    )
    parser.add_argument("--ticks", type=int, default=200)
    parser.add_argument("--ttl", action="store_true", default=True)
    parser.add_argument("--random-progression", action="store_true", default=True)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v5_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        enable_ttl=args.ttl,
        random_progression=args.random_progression,
        export_csv=args.export_csv,
    )


if __name__ == "__main__":
    main()
