# sim_manager/process_store.py
from __future__ import annotations

import itertools
import os
import platform
import signal
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ClientProcess:
    pid: int
    port: int
    cp_id: str
    city: Optional[str] = None


class ProcessStore:
    def __init__(self, start_port: int = 8101):
        # Sonradan base_port'ı değiştirmek için setter da koyduk
        self._base_port = start_port
        self._seq = itertools.count(start_port)
        self.clients: Dict[str, ClientProcess] = {}

    @property
    def base_port(self) -> int:
        return self._base_port

    def set_base_port(self, start_port: int) -> None:
        self._base_port = start_port
        self._seq = itertools.count(start_port)

    def next_port(self) -> int:
        return next(self._seq)

    @staticmethod
    def kill_pid(pid: int) -> None:
        try:
            if platform.system() == "Windows":
                os.system(f"taskkill /PID {pid} /F >NUL 2>&1")
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass


store = ProcessStore()
