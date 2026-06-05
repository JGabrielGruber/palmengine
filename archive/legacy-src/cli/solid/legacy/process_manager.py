"""
ProcessManager - manages long-running worker processes.

Uses Python's multiprocessing module. Each wizard session or background
workflow can be offloaded to a dedicated process for isolation and CPU usage.

For the initial skeleton this is a pragmatic implementation that:
- Spawns simple target functions
- Tracks PIDs and basic lifecycle
- Uses the DB as the source of truth for state
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from palm.cli.solid.legacy.exceptions import ProcessManagerError
from palm.config.settings import settings


@dataclass
class ManagedProcess:
    pid: int
    name: str
    status: str = "running"  # running, stopped, failed
    exit_code: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ProcessManager:
    """
    Lightweight multiprocessing manager.

    Not a full process pool (yet). Good enough for daemon + REPL usage.
    """

    def __init__(self, max_processes: int | None = None) -> None:
        self.max_processes = max_processes or settings.max_concurrent_processes
        self._processes: dict[str, ManagedProcess] = {}
        self._mp_processes: dict[str, mp.Process] = {}
        self._lock = mp.Lock()

    def spawn(
        self,
        target: Callable[..., Any],
        *,
        name: str | None = None,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Spawn a new child process. Returns internal process id (not OS pid)."""
        if len(self._processes) >= self.max_processes:
            raise ProcessManagerError("Maximum concurrent processes reached")

        proc_name = name or f"proc-{len(self._processes) + 1}"
        proc_id = f"{proc_name}-{id(target)}"

        p = mp.Process(target=target, args=args, kwargs=kwargs or {}, name=proc_name, daemon=True)
        p.start()

        managed = ManagedProcess(pid=p.pid, name=proc_name)
        with self._lock:
            self._processes[proc_id] = managed
            self._mp_processes[proc_id] = p

        return proc_id

    def status(self, proc_id: str) -> ManagedProcess | None:
        with self._lock:
            if proc_id not in self._processes:
                return None

            mp_proc = self._mp_processes.get(proc_id)
            managed = self._processes[proc_id]

            if mp_proc and not mp_proc.is_alive():
                managed.status = "stopped" if mp_proc.exitcode == 0 else "failed"
                managed.exit_code = mp_proc.exitcode

            return managed

    def list(self) -> list[dict[str, Any]]:
        result = []
        for pid, managed in list(self._processes.items()):
            mp_proc = self._mp_processes.get(pid)
            alive = mp_proc.is_alive() if mp_proc else False
            result.append(
                {
                    "id": pid,
                    "name": managed.name,
                    "os_pid": managed.pid,
                    "alive": alive,
                    "status": managed.status,
                    "exit_code": managed.exit_code,
                }
            )
        return result

    def terminate(self, proc_id: str, timeout: float = 5.0) -> bool:
        with self._lock:
            mp_proc = self._mp_processes.get(proc_id)
            if not mp_proc:
                return False
            if mp_proc.is_alive():
                mp_proc.terminate()
                mp_proc.join(timeout=timeout)
            self._processes.pop(proc_id, None)
            self._mp_processes.pop(proc_id, None)
            return True

    def shutdown_all(self, timeout: float = 10.0) -> None:
        for proc_id in list(self._mp_processes.keys()):
            self.terminate(proc_id, timeout=timeout)
