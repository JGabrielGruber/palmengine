#!/usr/bin/env python3
from __future__ import annotations

import sys
import threading
import traceback


def main() -> int:
    print("TODO: starting Palm TodoEngine …", flush=True)
    try:
        from todo_engine import TodoEngine
    except Exception:
        print("FAIL: import todo_engine", flush=True)
        traceback.print_exc()
        return 2

    engine = TodoEngine()
    try:
        engine.start()
        print("TODO: ApplicationHost started", flush=True)
        items = engine.list_todos()
        print(f"TODO: seeded list len={len(items)}", flush=True)
        # Keep interpreter alive for bridge / logcat.
        threading.Event().wait()
        return 0
    except Exception:
        print("FAIL: runtime error", flush=True)
        traceback.print_exc()
        try:
            engine.shutdown()
        except Exception:
            traceback.print_exc()
        # Still hold so logcat can capture FAIL.
        threading.Event().wait()
        return 3


if __name__ == "__main__":
    sys.exit(main())
