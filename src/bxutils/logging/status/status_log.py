import sys
import os
import platform
import json
from datetime import datetime
from pip._internal.operations.freeze import freeze
from typing import List

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import OS_VERSION
from bxcommon.utils import config
from bxcommon.utils import model_loader
from bxutils.encoding.json_encoder import EnhancedJSONEncoder
from bxutils.logging.status.analysis import Analysis
from bxutils.logging.status.blockchain_connection import BlockchainConnection
from bxutils.logging.status.diagnostics import Diagnostics
from bxutils.logging.status.environment import Environment
from bxutils.logging.status.extension_modules_state import ExtensionModulesState
from bxutils.logging.status.gateway_status import GatewayStatus
from bxutils.logging.status.installation_type import InstallationType
from bxutils.logging.status.network import Network
from bxutils.logging.status.relay_connection import RelayConnection
from bxutils.logging.status.summary import Summary

STATUS_FILE_NAME = "bloxroute_status.log"
CONN_TYPES = {ConnectionType.RELAY_BLOCK, ConnectionType.RELAY_TRANSACTION, ConnectionType.BLOCKCHAIN_NODE,
              ConnectionType.REMOTE_BLOCKCHAIN_NODE}


def initialize(use_ext: bool, src_ver: str) -> None:
    current_time = _get_current_time()
    summary = Summary(gateway_status=GatewayStatus.OFFLINE)
    environment = Environment(_get_installation_type(), OS_VERSION, platform.python_version(), sys.executable)
    block_relay = RelayConnection(connection_time=current_time)
    transaction_relay = RelayConnection(connection_time=current_time)
    blockchain_node = BlockchainConnection(connection_time=current_time)
    remote_blockchain_node = BlockchainConnection(connection_time=current_time)
    network = Network(block_relay, transaction_relay, blockchain_node, remote_blockchain_node)
    analysis = Analysis(current_time, _get_startup_param(), src_ver, _check_extensions_validity(use_ext, src_ver),
                        environment, network, _get_installed_python_modules())
    diagnostics = Diagnostics(summary, analysis)

    _save_status_to_file(diagnostics)


def update(conn_pool: ConnectionPool, use_ext: bool, src_ver: str) -> None:
    path = config.get_data_file(STATUS_FILE_NAME)
    if not os.path.exists(path):
        initialize(use_ext, src_ver)
    diagnostics = _load_status_from_file()
    analysis = diagnostics.analysis
    network = analysis.network

    current_conn_types = set()
    for conn_type in CONN_TYPES:
        for conn in conn_pool.get_by_connection_type(conn_type):
            if conn_type not in current_conn_types:
                current_conn_types.add(conn_type)
            network.update_connection(conn.CONNECTION_TYPE, conn.peer_desc, conn.fileno, conn.peer_id)

    for conn_type in CONN_TYPES - current_conn_types:
        network.update_connection(conn_type)

    summary = network.get_summary()
    diagnostics = Diagnostics(summary, analysis)

    _save_status_to_file(diagnostics)


def _check_extensions_validity(use_ext: bool, src_ver: str) -> ExtensionModulesState:
    if use_ext:
        try:
            import task_pool_executor as tpe  # pyre-ignore
        except ImportError:
            return ExtensionModulesState.UNAVAILABLE
        extensions_version = tpe.__version__
        if src_ver == extensions_version:
            return ExtensionModulesState.OK
        else:
            return ExtensionModulesState.INVALID_VERSION
    return ExtensionModulesState.UNAVAILABLE


def _get_current_time() -> str:
    return "UTC " + str(datetime.utcnow())


def _get_installation_type() -> InstallationType:
    if os.path.exists("/.dockerenv"):
        return InstallationType.DOCKER
    else:
        return InstallationType.PYPI


def _get_installed_python_modules() -> List[str]:
    installed_packages = []
    for name, module in sorted(sys.modules.items()):
        if hasattr(module, "__version__"):
            installed_packages.append(f"{name}=={module.__version__}")  # pyre-ignore
        else:
            installed_packages.append(name)
    return installed_packages


def _get_startup_param() -> str:
    return " ".join(sys.argv[1:])


def _load_status_from_file() -> Diagnostics:
    path = config.get_data_file(STATUS_FILE_NAME)
    with open(path, "r", encoding="utf-8") as json_file:
        status_file = json_file.read()
    return model_loader.load_model_from_json(Diagnostics, status_file)


def _save_status_to_file(diagnostics: Diagnostics) -> None:
    path = config.get_data_file(STATUS_FILE_NAME)
    with open(path, "w", encoding="utf-8") as outfile:
        json.dump(diagnostics, outfile, cls=EnhancedJSONEncoder, indent=2)