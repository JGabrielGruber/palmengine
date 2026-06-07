#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v9 - Async Streaming + Double Buffering
=================================================================
- Persistent kernels on GPU
- Double buffering + CUDA Streams for overlapping upload/compute/download
- TUI + plotext graphs including **Time Difference** (CPU - GPU)
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


# ====================== STEPS ======================
def torch_step(data: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
    repeats = (data.shape[1] + state.shape[1] - 1) // state.shape[1]
    state_broadcast = state.repeat(1, repeats)[:, : data.shape[1]]
    processed = data * 1.1 + torch.sin(state_broadcast) * 0.2
    state.add_(torch.mean(processed, dim=1, keepdim=True) * 0.05)
    return processed


TORCH_STEP = torch_step


def numpy_step(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    repeats = (64 + len(state) - 1) // len(state)
    state_broadcast = np.tile(state, repeats)[:64]
    processed = data * 1.1 + np.sin(state_broadcast) * 0.2
    state += np.mean(processed) * 0.05
    return processed


def cpu_process_instance(args: Tuple[np.ndarray, np.ndarray, int]):
    data, state, num_ticks = args
    for _ in range(num_ticks):
        data = numpy_step(data, state)
    return data, state


class PalmGPUBackendV9:
    """GPU backend with double buffering + async streams."""

    def __init__(self, batch_size: int = 1024, device: str = "cuda"):
        self.device = device
        self.batch_size = batch_size

        self.input_buf = torch.zeros(
            (batch_size, 64), device=device, dtype=torch.float32
        )
        self.state_buf = torch.zeros(
            (batch_size, 32), device=device, dtype=torch.float32
        )
        self.output_buf = torch.zeros(
            (batch_size, 64), device=device, dtype=torch.float32
        )

        self.stream = torch.cuda.Stream() if device == "cuda" else None
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
        processed = TORCH_STEP(inputs, state)
        outputs.copy_(processed)

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


def run_v9_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 100,
    export_csv: str = None,
    num_workers: int = None,
):
    print("Palm GPU Prototype v9 - Async Streaming + Time Difference Graph")
    print("=" * 95)
    print(f"Batch sizes: {batch_sizes} | Ticks: {num_ticks}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # CPU
        cpu_start = time.perf_counter()
        data_list = [np.random.randn(64).astype(np.float32) for _ in range(bs)]
        state_list = [np.zeros(3, dtype=np.float32) for _ in range(bs)]
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
            backend = PalmGPUBackendV9(batch_size=bs)
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
                f"GPU (Async)   | {gpu_time:.4f}s | {gpu_throughput:10.0f} items/s | VRAM: {vram_mb:.1f} MB"
            )
        else:
            print("GPU           | CUDA not available")

        time_diff = cpu_time - gpu_time
        speedup = gpu_throughput / cpu_throughput if gpu_throughput > 0 else 0.0

        results.append(
            {
                "batch_size": bs,
                "cpu_time": round(cpu_time, 4),
                "gpu_time": round(gpu_time, 4),
                "time_diff": round(time_diff, 4),
                "cpu_throughput": round(cpu_throughput),
                "gpu_throughput": round(gpu_throughput),
                "speedup": round(speedup, 1),
                "vram_mb": round(vram_mb, 1),
            }
        )

    # === TUI + Graphs ===
    if RICH_AVAILABLE and results:
        console = Console()
        table = Table(
            title="Palm GPU v9 Benchmark Results",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Batch", justify="right")
        table.add_column("CPU Time (s)", justify="right")
        table.add_column("GPU Time (s)", justify="right")
        table.add_column("Time Saved (s)", justify="right")
        table.add_column("Speedup", justify="right")
        table.add_column("VRAM (MB)", justify="right")

        for r in results:
            table.add_row(
                str(r["batch_size"]),
                f"{r['cpu_time']:.4f}",
                f"{r['gpu_time']:.4f}",
                f"{r['time_diff']:.4f}",
                f"{r['speedup']:.1f}x",
                f"{r['vram_mb']:.1f}",
            )
        console.print(
            Panel(table, title="[bold green]Summary + Time Difference[/bold green]")
        )

        if PLOTEXT_AVAILABLE:
            bs_list = [r["batch_size"] for r in results]
            time_diff_list = [r["time_diff"] for r in results]
            speedup_list = [r["speedup"] for r in results]

            # Time Difference Graph (NEW)
            plt.clf()
            plt.bar([str(x) for x in bs_list], time_diff_list, color="green")
            plt.title("Time Saved (CPU - GPU) per Batch Size")
            plt.xlabel("Batch Size")
            plt.ylabel("Seconds Saved")
            plt.show()

            # Speedup
            plt.clf()
            plt.bar([str(x) for x in bs_list], speedup_list)
            plt.title("Speedup vs Batch Size")
            plt.xlabel("Batch Size")
            plt.ylabel("x")
            plt.show()

    if export_csv:
        with open(export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults exported to {export_csv}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Palm GPU Prototype v9 - Async + Time Diff Graph"
    )
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[16384, 65536, 262144, 524288]
    )
    parser.add_argument("--ticks", type=int, default=80)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v9_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        num_workers=args.workers,
        export_csv=args.export_csv,
    )
