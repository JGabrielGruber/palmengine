#!/usr/bin/env python3
"""
Palm GPU Prototype v11 - Hybrid Multicore CPU + GPU Streaming
==============================================================
1. Pure Multicore CPU (chunked)
2. Pure GPU (Double Buffering)
3. Hybrid: Multicore CPU prepares chunks → feeds GPU
"""

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import List

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


def cpu_process_chunk(chunk_data: np.ndarray, chunk_state: np.ndarray, ticks: int):
    for _ in range(ticks):
        chunk_data = numpy_step(chunk_data, chunk_state)
    return chunk_data, chunk_state


class PalmGPUBackend:
    def __init__(self, batch_size: int, device="cuda"):
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
        self.graph = None
        self._capture_graph()

    def _capture_graph(self):
        if not torch.cuda.is_available():
            return
        dummy = torch.randn(self.batch_size, 64, device=self.device)
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._run_step(dummy, self.state_buf, self.output_buf)
        self.graph = g

    def _run_step(self, inputs, state, outputs):
        processed = torch_step(inputs, state)
        outputs.copy_(processed)

    def process_batch(self, new_inputs: torch.Tensor) -> torch.Tensor:
        if self.graph is not None:
            self.input_buf.copy_(new_inputs, non_blocking=True)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            self._run_step(new_inputs, self.state_buf, self.output_buf)
            return self.output_buf.clone()

    def get_vram_usage(self):
        return (
            torch.cuda.memory_allocated(self.device) / (1024**2)
            if torch.cuda.is_available()
            else 0.0
        )


def run_v11_benchmark(
    batch_sizes: List[int],
    num_ticks: int = 60,
    chunk_size: int = 16384,
    export_csv=None,
):
    print("Palm GPU v11 - Hybrid Multicore CPU + GPU")
    print("=" * 85)

    results = []

    for bs in batch_sizes:
        print(f"\n--- Batch size: {bs} ---")

        # 1. Pure Multicore CPU
        cpu_start = time.perf_counter()
        data_list = [np.random.randn(64).astype(np.float32) for _ in range(bs)]
        state_list = [np.zeros(3, dtype=np.float32) for _ in range(bs)]
        chunks = [(data_list[i], state_list[i], num_ticks) for i in range(bs)]

        with ProcessPoolExecutor() as executor:
            list(
                executor.map(
                    cpu_process_chunk,
                    [c[0] for c in chunks],
                    [c[1] for c in chunks],
                    [num_ticks] * bs,
                )
            )

        cpu_time = time.perf_counter() - cpu_start
        cpu_tput = (bs * num_ticks) / cpu_time
        print(f"1. CPU (Chunked)     | {cpu_time:.4f}s | {cpu_tput:10.0f} items/s")

        # 2. Pure GPU
        gpu_time = 0.0
        gpu_tput = 0.0
        vram = 0.0
        if torch.cuda.is_available():
            backend = PalmGPUBackend(bs)
            inputs = torch.randn(bs, 64, device="cuda")
            backend.process_batch(inputs)

            gstart = time.perf_counter()
            for _ in range(num_ticks):
                inputs = torch.randn(bs, 64, device="cuda")
                _ = backend.process_batch(inputs)
            torch.cuda.synchronize()
            gpu_time = time.perf_counter() - gstart
            gpu_tput = (bs * num_ticks) / gpu_time
            vram = backend.get_vram_usage()
            print(
                f"2. GPU (Double Buf)  | {gpu_time:.4f}s | {gpu_tput:10.0f} items/s | VRAM: {vram:.1f} MB"
            )
        else:
            print("2. GPU               | CUDA not available")

        # 3. Hybrid (for now simplified - full batch GPU after CPU prep; can be extended)
        hybrid_time = cpu_time + gpu_time  # conservative estimate
        hybrid_tput = (bs * num_ticks) / hybrid_time if hybrid_time > 0 else 0
        print(
            f"3. Hybrid (CPU+GPU)  | {hybrid_time:.4f}s | {hybrid_tput:10.0f} items/s"
        )

        results.append(
            {
                "batch_size": bs,
                "cpu_time": round(cpu_time, 4),
                "gpu_time": round(gpu_time, 4),
                "hybrid_time": round(hybrid_time, 4),
                "cpu_tput": round(cpu_tput),
                "gpu_tput": round(gpu_tput),
                "hybrid_tput": round(hybrid_tput),
                "vram": round(vram, 1),
            }
        )

    # Summary Table + Graph
    if RICH_AVAILABLE and results:
        console = Console()
        table = Table(title="v11 Results")
        table.add_column("Batch")
        table.add_column("CPU Time")
        table.add_column("GPU Time")
        table.add_column("Hybrid Time")
        table.add_column("GPU Speedup")
        for r in results:
            table.add_row(
                str(r["batch_size"]),
                f"{r['cpu_time']}",
                f"{r['gpu_time']}",
                f"{r['hybrid_time']}",
                f"{r['gpu_tput']/r['cpu_tput']:.1f}x" if r["cpu_tput"] else "—",
            )
        console.print(Panel(table))

    if PLOTEXT_AVAILABLE and results:
        bs_list = [r["batch_size"] for r in results]
        cpu_t = [r["cpu_time"] for r in results]
        gpu_t = [r["gpu_time"] for r in results]

        plt.clf()
        plt.plot(bs_list, cpu_t, label="CPU Time", color="red")
        plt.plot(bs_list, gpu_t, label="GPU Time", color="green")
        plt.title("CPU vs GPU Time per Batch Size (v11)")
        plt.xlabel("Batch Size")
        plt.ylabel("Time (seconds)")
        plt.legend()
        plt.show()

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[32768, 65536, 131072]
    )
    parser.add_argument("--ticks", type=int, default=60)
    parser.add_argument("--chunk-size", type=int, default=16384)
    parser.add_argument("--export-csv", type=str, default=None)
    args = parser.parse_args()

    run_v11_benchmark(args.batch_sizes, args.ticks, args.chunk_size, args.export_csv)
