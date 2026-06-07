#!/usr/bin/env python3
"""
Palm Engine GPU Prototype v10 - Double Buffering + Async Streams
================================================================
- Persistent kernels + double buffering
- CUDA Streams for overlapping upload/compute/download
- Clean single graph: CPU vs GPU time difference (line)
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
    processed = data * 1.12 + torch.sin(state_broadcast) * 0.15
    state.add_(torch.mean(processed, dim=1, keepdim=True) * 0.04)
    return processed


def numpy_step(data: np.ndarray, state: np.ndarray) -> np.ndarray:
    repeats = (64 + len(state) - 1) // len(state)
    state_broadcast = np.tile(state, repeats)[:64]
    processed = data * 1.12 + np.sin(state_broadcast) * 0.15
    state += np.mean(processed) * 0.04
    return processed


def cpu_process_instance(args: Tuple[np.ndarray, np.ndarray, int]):
    data, state, num_ticks = args
    for _ in range(num_ticks):
        data = numpy_step(data, state)
    return data, state


class PalmGPUBackendV10:
    """Double-buffered async GPU backend."""

    def __init__(self, batch_size: int = 1024, device: str = "cuda"):
        self.device = device
        self.batch_size = batch_size

        # Double buffers
        self.input_bufs = [
            torch.zeros((batch_size, 64), device=device, dtype=torch.float32),
            torch.zeros((batch_size, 64), device=device, dtype=torch.float32),
        ]
        self.state_bufs = [
            torch.zeros((batch_size, 32), device=device, dtype=torch.float32),
            torch.zeros((batch_size, 32), device=device, dtype=torch.float32),
        ]
        self.output_bufs = [
            torch.zeros((batch_size, 64), device=device, dtype=torch.float32),
            torch.zeros((batch_size, 64), device=device, dtype=torch.float32),
        ]

        self.stream = torch.cuda.Stream() if device == "cuda" else None
        self.current_buffer = 0
        self.graphs = [None, None]
        self._capture_graphs()

    def _capture_graphs(self):
        if not torch.cuda.is_available():
            return

        for i in range(2):
            dummy = torch.randn(self.batch_size, 64, device=self.device)
            self._run_step(dummy, self.state_bufs[i], self.output_bufs[i])

            g = torch.cuda.CUDAGraph()
            with torch.cuda.graph(g):
                self._run_step(
                    self.input_bufs[i], self.state_bufs[i], self.output_bufs[i]
                )
            self.graphs[i] = g

    def _run_step(self, inputs, state, outputs):
        processed = torch_step(inputs, state)
        outputs.copy_(processed)

    def process_tick(self, new_inputs: torch.Tensor) -> torch.Tensor:
        buf = self.current_buffer
        self.input_bufs[buf].copy_(new_inputs, non_blocking=True)

        if self.graphs[buf] is not None:
            with torch.cuda.stream(self.stream):
                self.graphs[buf].replay()
        else:
            self._run_step(
                self.input_bufs[buf], self.state_bufs[buf], self.output_bufs[buf]
            )

        self.current_buffer = 1 - buf
        return self.output_bufs[buf].clone()

    def get_vram_usage(self) -> float:
        return (
            torch.cuda.memory_allocated(self.device) / (1024**2)
            if torch.cuda.is_available()
            else 0.0
        )


def run_v10_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 80,
    export_csv: str = None,
    num_workers: int = None,
):
    print("Palm GPU Prototype v10 - Double Buffering + Async")
    print("=" * 90)
    print(f"Batch sizes: {batch_sizes} | Ticks: {num_ticks}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # CPU
        data_list = [np.random.randn(64).astype(np.float32) for _ in range(bs)]
        cpu_start = time.perf_counter()
        state_list = [np.zeros(3, dtype=np.float32) for i in range(bs)]
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
            backend = PalmGPUBackendV10(batch_size=bs)
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
                f"GPU (Double Buf) | {gpu_time:.4f}s | {gpu_throughput:10.0f} items/s | VRAM: {vram_mb:.1f} MB"
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
                "speedup": round(speedup, 1),
                "vram_mb": round(vram_mb, 1),
            }
        )

    # === Output ===
    if RICH_AVAILABLE and results:
        console = Console()
        table = Table(
            title="v10 - Double Buffering Results",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Batch", justify="right")
        table.add_column("CPU Time", justify="right")
        table.add_column("GPU Time", justify="right")
        table.add_column("Time Diff (s)", justify="right")
        table.add_column("Speedup", justify="right")

        for r in results:
            table.add_row(
                str(r["batch_size"]),
                f"{r['cpu_time']:.4f}",
                f"{r['gpu_time']:.4f}",
                f"{r['time_diff']:.4f}",
                f"{r['speedup']:.1f}x",
            )
        console.print(Panel(table))

    if PLOTEXT_AVAILABLE and results:
        bs_list = [str(r["batch_size"]) for r in results]
        cpu_times = [r["cpu_time"] for r in results]
        gpu_times = [r["gpu_time"] * 10 for r in results]

        # Single focused line graph as requested

        plt.simple_multiple_bar(
            bs_list,
            [cpu_times, gpu_times],
            width=100,
            labels=["CPU", "GPU x 10"],
            title="Processing Time per Batch",
        )

        plt.show()

    if export_csv:
        with open(export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults exported to {export_csv}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Palm GPU v10 - Double Buffering")
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[32768, 65536, 131072, 262144]
    )
    parser.add_argument("--ticks", type=int, default=60)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v10_benchmark(
        batch_sizes=args.batch_sizes,
        num_ticks=args.ticks,
        num_workers=args.workers,
        export_csv=args.export_csv,
    )
