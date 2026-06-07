"""
Palm Engine GPU Prototype Demo
==============================
Simple demonstration of GPU-accelerated vector-of-steps processing
with persistent state and CUDA Graphs (PyTorch).

Run locally on machine with NVIDIA GPU + CUDA.
"""

import argparse
import random
import sys
import time
from typing import List, Tuple

import numpy as np
import torch


def cpu_vector_step(
    data: np.ndarray, state: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Simple CPU vectorized 'step' simulation: process + update state."""
    # Simulate some computation: e.g., transform + accumulate
    # Match dimensions for broadcasting (data is wider)
    state_broadcast = np.tile(state, (1, data.shape[1] // state.shape[1]))
    if state_broadcast.shape[1] < data.shape[1]:
        state_broadcast = np.pad(
            state_broadcast,
            ((0, 0), (0, data.shape[1] - state_broadcast.shape[1])),
            mode="constant",
        )
    processed = data * 1.5 + np.sin(state_broadcast)
    new_state = (
        state + np.mean(processed, axis=1, keepdims=True) * 0.1
    )  # Update state consistently
    return processed, new_state


class GPUBackend:
    def __init__(self, batch_size: int = 1024, device: str = "cuda"):
        self.device = device
        self.batch_size = batch_size
        # Fixed persistent buffers
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
        self.stream = torch.cuda.Stream() if device == "cuda" else None
        self._capture_graph()

    def _capture_graph(self):
        """Capture CUDA Graph for repeated execution on fixed buffers."""
        if self.device != "cuda" or not torch.cuda.is_available():
            print("Warning: CUDA not available, falling back to eager mode.")
            return

        # Warmup
        self._vectorized_step(self.input_buf, self.state_buf, self.output_buf)

        # Capture graph
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            self._vectorized_step(self.input_buf, self.state_buf, self.output_buf)
        self.graph = g

    def _vectorized_step(
        self, inputs: torch.Tensor, state: torch.Tensor, outputs: torch.Tensor
    ):
        """Vectorized step on GPU (PyTorch ops simulating Palm step)."""
        # Match CPU logic: broadcast/pad state to inputs width
        state_width = state.shape[1]
        input_width = inputs.shape[1]
        repeats = (input_width + state_width - 1) // state_width
        state_broadcast = state.repeat(1, repeats)[:, :input_width]

        processed = inputs * 1.5 + torch.sin(state_broadcast)
        new_state = state + torch.mean(processed, dim=1, keepdim=True) * 0.1

        outputs.copy_(processed)
        state.copy_(new_state)

    def process_batch(self, new_inputs: torch.Tensor) -> torch.Tensor:
        """Feed input to fixed buffer and replay graph."""
        if self.graph is not None:
            self.input_buf.copy_(new_inputs)
            self.graph.replay()
            return self.output_buf.clone()
        else:
            # Fallback
            self.input_buf.copy_(new_inputs)
            self._vectorized_step(self.input_buf, self.state_buf, self.output_buf)
            return self.output_buf.clone()


def benchmark_cpu(batch_sizes: List[int], num_steps: int = 100):
    print("\n=== CPU Benchmark ===")
    results = []
    for bs in batch_sizes:
        data = np.random.randn(bs, 64).astype(np.float32)
        state = np.zeros((bs, 32), dtype=np.float32)
        start = time.perf_counter()
        for _ in range(num_steps):
            data, state = cpu_vector_step(data, state)
        elapsed = time.perf_counter() - start
        throughput = (bs * num_steps) / elapsed
        print(
            f"Batch {bs:5d} | Time: {elapsed:.4f}s | Throughput: {throughput:8.0f} items/sec"
        )
        results.append(throughput)
    return results


def benchmark_gpu(batch_sizes: List[int], num_steps: int = 100):
    print("\n=== GPU Benchmark (PyTorch + CUDA Graph) ===")
    if not torch.cuda.is_available():
        print("CUDA not available. Skipping GPU benchmark.")
        return []

    results = []
    for bs in batch_sizes:
        backend = GPUBackend(batch_size=bs)
        inputs = torch.randn(bs, 64, device="cuda", dtype=torch.float32)

        # Warmup
        backend.process_batch(inputs)

        start = time.perf_counter()
        for _ in range(num_steps):
            inputs = torch.randn(
                bs, 64, device="cuda", dtype=torch.float32
            )  # Simulate new data
            _ = backend.process_batch(inputs)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        throughput = (bs * num_steps) / elapsed
        print(
            f"Batch {bs:5d} | Time: {elapsed:.4f}s | Throughput: {throughput:8.0f} items/sec"
        )
        results.append(throughput)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Palm Engine GPU Prototype - Benchmark Vector Steps"
    )
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[64, 256, 1024, 4096, 8192],
        help="Batch sizes to test",
    )
    parser.add_argument(
        "--steps", type=int, default=200, help="Number of steps per benchmark"
    )
    parser.add_argument(
        "--compare", action="store_true", default=True, help="Run both CPU and GPU"
    )
    args = parser.parse_args()

    print("Palm GPU Prototype Demo")
    print("======================")
    print(f"Testing batch sizes: {args.batch_sizes}")
    print(f"Steps per run: {args.steps}\n")

    if args.compare:
        cpu_results = benchmark_cpu(args.batch_sizes, args.steps)
        gpu_results = benchmark_gpu(args.batch_sizes, args.steps)

        print("\n=== Summary ===")
        for bs, c, g in zip(
            args.batch_sizes,
            cpu_results or [0] * len(args.batch_sizes),
            gpu_results or [0] * len(args.batch_sizes),
        ):
            speedup = g / c if c > 0 else 0
            print(
                f"Batch {bs:5d} | CPU: {c:8.0f} | GPU: {g:8.0f} | Speedup: {speedup:.1f}x"
            )
    else:
        benchmark_gpu(args.batch_sizes, args.steps)

    print("\nInsights:")
    print("- Larger batches = better GPU utilization")
    print("- Persistent buffers + CUDA Graphs minimize overhead")
    print("- Adapt this pattern to Palm's step vector / BT nodes")


if __name__ == "__main__":
    main()
