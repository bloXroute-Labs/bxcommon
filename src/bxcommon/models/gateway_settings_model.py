from dataclasses import dataclass


@dataclass
class GatewaySettingsModel:
    min_peer_relays_count: int = 1
