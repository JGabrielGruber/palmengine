"""
Palm Engine GPU Prototype v2 - Enhanced Testing
===============================================
Advanced benchmark for GPU-accelerated vector-of-steps with:
- Persistent VRAM state + CUDA Graphs
- TTL (time-to-live) simulation for ERP-like data
- VRAM usage tracking
- More realistic Palm-style step simulation
- Detailed reporting + optional CSV export

Run on NVIDIA GPU with CUDA + PyTorch (cuXXX)
"""

import argparse
import csv
import time
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import torch


def cpu_vector_step(
    data: np.ndarray, state: np.ndarray, timestamps: np.ndarray = None, ttl: int = 1000
) -> tuple:
    """CPU baseline with optional TTL eviction."""
    state_broadcast = np.tile(state, (1, data.shape[1] // state.shape[1] + 1))[
        :, : data.shape[1]
    ]
    processed = data * 1.5 + np.sin(state_broadcast)

    if timestamps is not None:
        current_time = time.time()
        expired = (current_time - timestamps) > ttl
        processed[expired] = 0.0  # Evict expired entries

    new_state = state + np.mean(processed, axis=1, keepdims=True) * 0.1
    return processed, new_state


class GPUBackend:
    def __init__(
        self,
        batch_size: int = 1024,
        device: str = "cuda",
        state_dim: int = 32,
        data_dim: int = 64,
        enable_ttl: bool = True,
    ):
        self.device = device
        self.batch_size = batch_size
        self.state_dim = state_dim
        self.data_dim = data_dim
        self.enable_ttl = enable_ttl

        # Fixed persistent buffers in VRAM
        self.input_buf = torch.zeros(
            (batch_size, data_dim), device=device, dtype=torch.float32
        )
        self.state_buf = torch.zeros(
            (batch_size, state_dim), device=device, dtype=torch.float32
        )
        self.output_buf = torch.zeros(
            (batch_size, data_dim), device=device, dtype=torch.float32
        )

        if enable_ttl:
            self.timestamp_buf = torch.zeros(
                batch_size, device=device, dtype=torch.float32
            )
            self.ttl = 5.0  # seconds for demo

        self.graph = None
        self._capture_graph()

    def _capture_graph(self):
        if self.device != "cuda" or not torch.cuda.is_available():
            print("Warning: CUDA not available. Using eager fallback.")
            return

        # Warmup
        dummy = torch.randn(self.batch_size, self.data_dim, device=self.device)
        self.process_batch(dummy)

        # Capture CUDA Graph
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._vectorized_step(self.input_buf, self.state_buf, self.output_buf)
        self.graph = g

    def _vectorized_step(
        self, inputs: torch.Tensor, state: torch.Tensor, outputs: torch.Tensor
    ):
        # Broadcast state to match input width
        state_width = state.shape[1]
        repeats = (inputs.shape[1] + state_width - 1) // state_width
        state_broadcast = state.repeat(1, repeats)[:, : inputs.shape[1]]

        processed = inputs * 1.5 + torch.sin(state_broadcast)

        if self.enable_ttl and hasattr(self, "timestamp_buf"):
            current_time = time.time()
            expired_mask = (current_time - self.timestamp_buf) > self.ttl
            processed[expired_mask] = 0.0

        new_state = state + torch.mean(processed, dim=1, keepdim=True) * 0.1

        outputs.copy_(processed)
        state.copy_(new_state)

        if self.enable_ttl and hasattr(self, "timestamp_buf"):
            self.timestamp_buf[:] = current_time

    def process_batch(self, new_inputs: torch.Tensor) -> torch.Tensor:
        if self.graph is not None:
            self.input_buf.copy_(new_inputs)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            self.input_buf.copy_(new_inputs)
            self._vectorized_step(self.input_buf, self.state_buf, self.output_buf)
            return self.output_buf.clone()

    def get_vram_usage(self) -> float:
        if self.device == "cuda" and torch.cuda.is_available():
            return torch.cuda.memory_allocated(self.device) / (1024**2)  # MB
        return 0.0


def run_benchmark(
    batch_sizes: List[int],
    num_steps: int = 200,
    enable_ttl: bool = True,
    export_csv: str = None,
):
    print("Palm GPU Prototype v2 - Enhanced Benchmark")
    print("=" * 50)
    print(f"Batch sizes: {batch_sizes}")
    print(f"Steps per batch: {num_steps}")
    print(f"TTL enabled: {enable_ttl}")
    print()

    results = []

    for bs in batch_sizes:
        print(f"\n--- Testing batch size: {bs} ---")

        # CPU
        cpu_start = time.perf_counter()
        data = np.random.randn(bs, 64).astype(np.float32)
        state = np.zeros((bs, 32), dtype=np.float32)
        ts = np.full(bs, time.time()) if enable_ttl else None

        for _ in range(num_steps):
            data, state = cpu_vector_step(data, state, ts, ttl=5)
        cpu_time = time.perf_counter() - cpu_start
        cpu_throughput = (bs * num_steps) / cpu_time

        print(
            f"CPU  | Time: {cpu_time:.4f}s | Throughput: {cpu_throughput:10.0f} items/s"
        )

        # GPU
        gpu_throughput = 0
        gpu_time = 0
        vram_mb = 0

        if torch.cuda.is_available():
            backend = GPUBackend(batch_size=bs, enable_ttl=enable_ttl)
            inputs = torch.randn(bs, 64, device="cuda")

            # Warmup + capture
            backend.process_batch(inputs)

            gpu_start = time.perf_counter()
            for _ in range(num_steps):
                inputs = torch.randn(bs, 64, device="cuda")
                _ = backend.process_batch(inputs)
            torch.cuda.synchronize()
            gpu_time = time.perf_counter() - gpu_start
            gpu_throughput = (bs * num_steps) / gpu_time
            vram_mb = backend.get_vram_usage()

            print(
                f"GPU  | Time: {gpu_time:.4f}s | Throughput: {gpu_throughput:10.0f} items/s | VRAM: {vram_mb:.1f} MB"
            )
        else:
            print("GPU  | CUDA not available — skipped")

        speedup = gpu_throughput / cpu_throughput if gpu_throughput > 0 else 0

        result = {
            "batch_size": bs,
            "cpu_time": cpu_time,
            "cpu_throughput": cpu_throughput,
            "gpu_time": gpu_time,
            "gpu_throughput": gpu_throughput,
            "speedup": speedup,
            "vram_mb": vram_mb,
            "ttl_enabled": enable_ttl,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(
            f"Batch {r['batch_size']:5d} | CPU: {r['cpu_throughput']:10.0f} | GPU: {r['gpu_throughput']:10.0f} | Speedup: {r['speedup']:.1f}x | VRAM: {r['vram_mb']:.1f}MB"
        )

    if export_csv:
        with open(export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults exported to {export_csv}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Palm Engine GPU Prototype v2")
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[64, 256, 1024, 4096, 8192]
    )
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument(
        "--ttl", action="store_true", default=True, help="Enable TTL simulation"
    )
    parser.add_argument(
        "--export-csv", type=str, default=None, help="Export results to CSV file"
    )
    args = parser.parse_args()

    run_benchmark(
        batch_sizes=args.batch_sizes,
        num_steps=args.steps,
        enable_ttl=args.ttl,
        export_csv=args.export_csv,
    )


if __name__ == "__main__":
    main()
