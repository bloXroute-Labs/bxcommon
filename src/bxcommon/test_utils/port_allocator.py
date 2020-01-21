import socket
from typing import Optional
from contextlib import closing

from bxcommon.network.port_range import PortRange


def check_port(port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(("", port))
        except socket.error:
            return False
        else:
            return True


class PortAllocator:

    def __init__(self, port_range: PortRange):
        self._port_range = port_range
        self._last_allocated_port: Optional[int] = None

    def allocate(self) -> int:
        port = self._get_next_port()
        self._last_allocated_port = port
        return port

    def _get_next_port(self, port: Optional[int] = None) -> int:
        if port is None:
            port = self._port_range.start if self._last_allocated_port is None else self._last_allocated_port + 1
        if port not in self._port_range:
            raise RuntimeError(f"No available ports remained in range: {self._port_range}!")
        elif check_port(port):
            return port
        else:
            return self._get_next_port(port + 1)