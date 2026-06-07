#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v7 - TUI Dashboard with Graphs
========================================================
- Rich TUI tables
- Multiple plotext graphs including CPU vs GPU comparison
"""

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import List, Tuple

import numpy as np
import torch

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import plotext as plt

    PLOTEXT_AVAILABLE = True
except ImportError:
    PLOTEXT_AVAILABLE = False


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


# NumPy Steps (CPU)
def numpy_step_validate(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    return data * 0.98


def numpy_step_reserve(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    reserved = data * 0.82
    state_update = np.mean(reserved) * 0.04
    state += state_update
    return reserved


def numpy_step_calculate(data: np.ndarray, state: np.ndarray) -> np.ndarray:
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
    data, state, num_ticks = args
    step_idx = int(state[0])
    for _ in range(num_ticks):
        s = step_idx % 4
        data = NUMPY_STEPS[s](data, state)
        step_idx = (step_idx + 1) % 4
    state[0] = step_idx
    return data, state


class PalmGPUBackendV7:
    # ... (same as before - unchanged for brevity)
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


def run_v7_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 200,
    random_progression: bool = True,
    export_csv: str = None,
    num_workers: int = None,
):
    console = Console() if RICH_AVAILABLE else None

    print("Palm GPU Prototype v7 - TUI Dashboard + CPU vs GPU Graph")
    print("=" * 90)
    print(f"Batch sizes: {batch_sizes} | Ticks: {num_ticks}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # CPU
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
            backend = PalmGPUBackendV7(
                batch_size=bs, random_progression=random_progression
            )
            inputs = torch.randn(bs, 64, device="cuda")
            backend.process_tick(inputs)

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
                "cpu_throughput": round(cpu_throughput),
                "gpu_throughput": round(gpu_throughput),
                "speedup": round(speedup, 1),
                "vram_mb": round(vram_mb, 1),
            }
        )

    # === TUI Dashboard ===
    if RICH_AVAILABLE and results:
        console = Console()
        table = Table(
            title="Palm GPU v7 Benchmark Results",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Batch", justify="right")
        table.add_column("CPU items/s", justify="right")
        table.add_column("GPU items/s", justify="right")
        table.add_column("Speedup", justify="right")
        table.add_column("VRAM (MB)", justify="right")

        for r in results:
            table.add_row(
                str(r["batch_size"]),
                f"{r['cpu_throughput']:,}",
                f"{r['gpu_throughput']:,}",
                f"{r['speedup']:.1f}x",
                f"{r['vram_mb']:.1f}",
            )

        console.print(Panel(table, title="[bold green]Summary Table[/bold green]"))

        if PLOTEXT_AVAILABLE:
            bs_list = [r["batch_size"] for r in results]
            cpu_list = [r["cpu_throughput"] for r in results]
            gpu_list = [r["gpu_throughput"] for r in results]

            # 1. GPU Throughput
            plt.clf()
            plt.plot(bs_list, gpu_list, marker="braille", color="green")
            plt.title("GPU Throughput vs Batch Size")
            plt.xlabel("Batch Size")
            plt.ylabel("Items / sec")
            plt.show()

            # 2. VRAM
            plt.clf()
            plt.plot(
                bs_list, [r["vram_mb"] for r in results], marker="braille", color="cyan"
            )
            plt.title("VRAM Usage vs Batch Size")
            plt.xlabel("Batch Size")
            plt.ylabel("MB")
            plt.show()

            # 3. Speedup
            plt.clf()
            plt.bar([str(x) for x in bs_list], [r["speedup"] for r in results])
            plt.title("Speedup vs Batch Size")
            plt.xlabel("Batch Size")
            plt.ylabel("x")
            plt.show()

            # 4. NEW: CPU vs GPU Comparison
            plt.clf()
            plt.plot(
                bs_list, cpu_list, label="CPU Multicore", marker="braille", color="red"
            )
            plt.plot(bs_list, gpu_list, label="GPU", marker="braille", color="green")
            plt.title("CPU vs GPU Throughput Comparison")
            plt.xlabel("Batch Size")
            plt.ylabel("Items / sec")
            plt.show()

        else:
            print("\n[Install plotext for graphs: pip install plotext]")

    if export_csv:
        with open(export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults exported to {export_csv}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Palm GPU Prototype v7 - TUI Dashboard"
    )
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[1024, 4096, 8192, 16384]
    )
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v7_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        num_workers=args.workers,
        export_csv=args.export_csv,
    )
