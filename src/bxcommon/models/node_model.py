from bxcommon.constants import MAX_COUNTRY_LENGTH
from dataclasses import dataclass


@dataclass
class NodeModel:
    def __init__(self, node_type=None, external_ip=None, external_port=None, network=None, online=None, node_id=None,
                 sid_start=None, sid_end=None, sid_expire_time=None, last_pong_time=None, is_gateway_miner=None,
                 is_internal_gateway=None, source_version=None, protocol_version=None, blockchain_network_num=None,
                 blockchain_ip=None, blockchain_port=None, node_public_key=None, hostname=None, sdn_id=None,
                 os_version=None, continent=None, country=None, split_relays=None, idx: int = None,
                 has_fully_updated_tx_service=False, node_start_time=None, baseline_route_redundancy: int = 0):
        self.external_port = external_port
        self.network = network
        self.online = online
        self.node_id = node_id
        self.sid_start = sid_start
        self.sid_end = sid_end
        self.sid_expire_time = sid_expire_time
        self.node_type = node_type
        self.external_ip = external_ip
        self.last_pong_time = last_pong_time
        self.is_gateway_miner = is_gateway_miner
        self.is_internal_gateway = is_internal_gateway
        self.source_version = source_version
        self.protocol_version = protocol_version
        self.blockchain_network_num = blockchain_network_num
        self.blockchain_ip = blockchain_ip
        self.blockchain_port = blockchain_port
        self.hostname = hostname
        self.sdn_id = sdn_id
        self.os_version = os_version
        self.continent = continent
        self.split_relays = split_relays
        if country is not None:
            self.country = country[:MAX_COUNTRY_LENGTH]
        else:
            self.country = None
        self.idx = idx
        self.sync_txs_status = has_fully_updated_tx_service
        self.node_start_time = node_start_time

        # Ethereum remote blockchain attribute
        self.node_public_key = node_public_key
        self.baseline_route_redundancy = baseline_route_redundancy
