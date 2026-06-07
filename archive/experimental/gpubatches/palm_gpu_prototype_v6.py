#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v6 - Fair Multicore CPU Baseline (Fixed)
============================================================
- Multicore CPU with ProcessPoolExecutor
- Fixed broadcasting in NumPy steps
"""

import argparse
import csv
import random
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import List, Tuple

import numpy as np
import torch


# Torch Steps (GPU)
def torch_step_validate(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    return data * 0.98


def torch_step_reserve(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    reserved = data * 0.82
    state_update = torch.mean(reserved, dim=1, keepdim=True) * 0.04
    state.add_(state_update)
    return reserved


def torch_step_calculate(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    repeats = (data.shape[1] + state.shape[1] - 1) // state.shape[1]
    state_broadcast = state.repeat(1, repeats)[:, : data.shape[1]]
    return data * 1.12 + torch.sin(state_broadcast)


def torch_step_commit(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    commit_val = data * 0.95
    state_update = torch.mean(commit_val, dim=1, keepdim=True) * 0.07
    state.add_(state_update)
    return commit_val


TORCH_STEPS = [
    torch_step_validate,
    torch_step_reserve,
    torch_step_calculate,
    torch_step_commit,
]


# NumPy Steps (CPU) - Fixed broadcasting
def numpy_step_validate(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    return data * 0.98


def numpy_step_reserve(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    reserved = data * 0.82
    state_update = np.mean(reserved) * 0.04
    state += state_update
    return reserved


def numpy_step_calculate(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    # Proper broadcasting: tile state to match data length (64)
    repeats = (64 + len(state) - 1) // len(state)
    state_broadcast = np.tile(state, repeats)[:64]
    return data * 1.12 + np.sin(state_broadcast)


def numpy_step_commit(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    commit_val = data * 0.95
    state_update = np.mean(commit_val) * 0.07
    state += state_update
    return commit_val


NUMPY_STEPS = [
    numpy_step_validate,
    numpy_step_reserve,
    numpy_step_calculate,
    numpy_step_commit,
]


def cpu_process_instance(args: Tuple[np.ndarray, np.ndarray, int]):
    """Single instance processing for multicore."""
    data, state, num_ticks = args
    step_idx = int(state[0])
    for _ in range(num_ticks):
        s = step_idx % 4
        data = NUMPY_STEPS[s](data, state)
        step_idx = (step_idx + 1) % 4
    state[0] = step_idx
    return data, state


class PalmGPUBackendV6:
    def __init__(
        self,
        batch_size: int = 1024,
        device: str = "cuda",
        random_progression: bool = True,
    ):
        self.device = device
        self.batch_size = batch_size
        self.random_progression = random_progression

        self.input_buf = torch.zeros(
            (batch_size, 64), device=device, dtype=torch.float32
        )
        self.state_buf = torch.zeros(
            (batch_size, 32), device=device, dtype=torch.float32
        )
        self.output_buf = torch.zeros(
            (batch_size, 64), device=device, dtype=torch.float32
        )
        self.step_index_buf = torch.zeros(batch_size, device=device, dtype=torch.long)

        self.graph = None
        self._capture_graph()

    def _capture_graph(self):
        if not torch.cuda.is_available():
            return
        dummy = torch.randn(self.batch_size, 64, device=self.device)
        self.process_tick(dummy)
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._gpu_tick(self.input_buf, self.state_buf, self.output_buf)
        self.graph = g

    def _gpu_tick(
        self, inputs: torch.Tensor, state: torch.Tensor, outputs: torch.Tensor
    ):
        current = inputs.clone()
        for step_idx in range(4):
            mask = self.step_index_buf == step_idx
            temp = TORCH_STEPS[step_idx](current, state)
            current = torch.where(mask.unsqueeze(1), temp, current)

        outputs.copy_(current)

        # Advance steps on GPU
        if self.random_progression:
            advance = (torch.rand(self.batch_size, device=self.device) > 0.4).long()
            self.step_index_buf.add_(advance)
            self.step_index_buf %= 4
        else:
            self.step_index_buf.add_(1)
            self.step_index_buf %= 4

    def process_tick(self, new_inputs: torch.Tensor) -> torch.Tensor:
        if self.graph is not None:
            self.input_buf.copy_(new_inputs)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            self.input_buf.copy_(new_inputs)
            self._gpu_tick(self.input_buf, self.state_buf, self.output_buf)
            return self.output_buf.clone()

    def get_vram_usage(self) -> float:
        return (
            torch.cuda.memory_allocated(self.device) / (1024**2)
            if torch.cuda.is_available()
            else 0.0
        )


def run_v6_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 200,
    random_progression: bool = True,
    export_csv: str = None,
    num_workers: int = None,
):
    print("Palm GPU Prototype v6 - Fair Multicore CPU Baseline (Fixed)")
    print("=" * 80)
    print(f"Batch sizes: {batch_sizes} | Ticks: {num_ticks}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # Multicore CPU
        cpu_start = time.perf_counter()
        data_list = [np.random.randn(64).astype(np.float32) for _ in range(bs)]
        state_list = [
            np.array([float(i % 4), 0.0], dtype=np.float32) for i in range(bs)
        ]

        chunks = [(data_list[i], state_list[i], num_ticks) for i in range(bs)]

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            list(executor.map(cpu_process_instance, chunks))

        cpu_time = time.perf_counter() - cpu_start
        cpu_throughput = (bs * num_ticks) / cpu_time
        print(f"CPU Multicore | {cpu_time:.4f}s | {cpu_throughput:10.0f} items/s")

        # GPU
        gpu_time = 0.0
        gpu_throughput = 0.0
        vram_mb = 0.0

        if torch.cuda.is_available():
            backend = PalmGPUBackendV6(
                batch_size=bs, random_progression=random_progression
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
                f"GPU           | {gpu_time:.4f}s | {gpu_throughput:10.0f} items/s | VRAM: {vram_mb:.1f} MB"
            )
        else:
            print("GPU           | CUDA not available")

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
            }
        )

    print("\n" + "=" * 80)
    print("SUMMARY - Palm GPU v6 (Multicore CPU vs GPU)")
    print("=" * 80)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Palm GPU Prototype v6")
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[64, 256, 1024, 4096, 8192]
    )
    parser.add_argument("--ticks", type=int, default=200)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v6_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        num_workers=args.workers,
        export_csv=args.export_csv,
    )
