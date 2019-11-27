from typing import NamedTuple


class IpEndpoint(NamedTuple):
    ip_address: str
    port: int

    def __repr__(self) -> str:
        return f"{self.ip_address} {self.port}"

    def __eq__(self, other: "IpEndpoint") -> bool:
        return self.ip_address == other.ip_address and self.port == other.port

    def __hash__(self):
        return hash((self.ip_address, self.port))
