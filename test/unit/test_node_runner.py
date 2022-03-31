import argparse
import os

from argparse import Namespace
from typing import Optional
from unittest import mock
from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon import constants, node_runner
from bxcommon.models.node_model import NodeModel
from bxcommon.models.node_type import NodeType
from bxcommon.test_utils import helpers
from bxcommon.utils import config
from bxcommon.common_opts import CommonOpts

from bxutils.logging import log_config
from bxutils.logging.log_format import LogFormat
from bxutils.logging.log_level import LogLevel
from bxutils.services.node_ssl_service import NodeSSLService


class NodeMock:
    NODE_TYPE = NodeType.EXTERNAL_GATEWAY

    def __init__(self, opts: Namespace, node_ssl_service: Optional[NodeSSLService] = None):
        self.opts: CommonOpts = opts
        self.node_ssl_service = node_ssl_service


class EventLoopMock:

    def __init__(self):
        self.run_count = 0

    async def run(self):
        self.run_count += 1

class EventLoopRestartMock:

    def __init__(self):
        self.run_count = 0

    async def run(self):
        self.run_count += 1


def get_mock_node():
    return NodeMock


class TestNodeRunner(AbstractTestCase):

    def setUp(self):
        self.blockchain_network = helpers.blockchain_network(
            protocol="Bitcoin",
            network_name="Mainnet",
            network_num=1,
            block_interval=600,
            final_tx_confirmations_count=6
        )
        self.set_ssl_folder()
        opts = {
            "log_path": "",
            "to_stdout": True,
            "external_port": 0,
            "external_ip": "1.1.1.1",
            "node_id": None,
            "blockchain_network": self.blockchain_network.network,
            "network_num": self.blockchain_network.network_num,
            "blockchain_protocol": self.blockchain_network.protocol,
            "blockchain_networks": {self.blockchain_network.network_num: self.blockchain_network},
            "log_level": LogLevel.INFO,
            "log_format": LogFormat.PLAIN,
            "log_flush_immediately": True,
            "log_fluentd_enable": False,
            "log_fluentd_host": None,
            "use_extensions": True,
            "log_fluentd_queue_size": 1000,
            "thread_pool_parallelism_degree": config.get_thread_pool_parallelism_degree(
                str(constants.DEFAULT_THREAD_POOL_PARALLELISM_DEGREE),
            ),
            "log_level_overrides": {},
            "source_version": "v1.0.0",
            "ca_cert_url": f"{self.ssl_folder_url}/ca",
            "private_ssl_base_url": self.ssl_folder_url,
            "data_dir": config.get_default_data_path(),
            "log_level_fluentd": LogLevel.DEBUG,
            "log_level_stdout": LogLevel.TRACE,
            "sdn_url": "https://localhost:8080",
        }
        for item in CommonOpts.__dataclass_fields__:
            if item not in opts:
                opts[item] = None
        self.opts = CommonOpts.from_opts(Namespace(**opts))
        log_config.create_logger(None, LogLevel.WARNING)
        self.event_loop_mock = EventLoopMock()

    @mock.patch("bxcommon.utils.cli.get_argument_parser")
    @mock.patch("bxcommon.utils.cli.parse_arguments")
    @mock.patch("bxcommon.services.sdn_http_service.fetch_blockchain_networks")
    @mock.patch("bxcommon.services.sdn_http_service.fetch_account_model")
    @mock.patch("bxcommon.node_runner.NodeEventLoop")
    @mock.patch("bxcommon.services.sdn_http_service.register_node")
    @mock.patch("bxcommon.utils.config.log_pid")
    def test_run_node(
            self,
            log_pid_mock,
            register_node_mock,
            create_event_loop_mock,
            fetch_account_model_mock,
            fetch_blockchain_networks_mock,
            get_argument_parser_mock,
            parse_arguments_mock,
    ):
        log_pid_mock.return_value = None

        node_runner._init_ssl_service = MagicMock()
        create_event_loop_mock.return_value = self.event_loop_mock
        register_node_mock.return_value = NodeModel(external_ip="1.1.1.1", external_port=1234, node_type=NodeType.RELAY)
        fetch_account_model_mock.return_value = None
        fetch_blockchain_networks_mock.return_value = [self.blockchain_network]
        get_argument_parser_mock.return_value = argparse.ArgumentParser()
        self.assertEqual(constants.SID_EXPIRE_TIME_SECONDS, self.opts.sid_expire_time)
        parse_arguments_mock.return_value = self.opts
        node_runner._init_ssl_service = MagicMock()
        node_runner.run_node("", self.opts, get_mock_node, NodeType.RELAY)
        self.assertEqual(self.event_loop_mock.run_count, 1)

    @mock.patch("bxcommon.utils.cli.get_argument_parser")
    @mock.patch("bxcommon.utils.cli.parse_arguments")
    @mock.patch("bxcommon.services.sdn_http_service.fetch_blockchain_networks")
    @mock.patch("bxcommon.services.sdn_http_service.fetch_account_model")
    @mock.patch("bxcommon.node_runner.NodeEventLoop")
    @mock.patch("bxcommon.services.sdn_http_service.register_node")
    @mock.patch("bxcommon.utils.config.log_pid")
    def test_run_node_init_tasks(
        self,
        log_pid_mock,
        register_node_mock,
        create_event_loop_mock,
        fetch_account_model_mock,
        fetch_blockchain_networks_mock,
        get_argument_parser_mock,
        parse_arguments_mock,
    ):
        log_pid_mock.return_value = None
        node_runner._init_ssl_service = MagicMock()
        create_event_loop_mock.return_value = self.event_loop_mock
        register_node_mock.return_value = NodeModel(
            external_ip="1.1.1.1", external_port=1234, node_type=NodeType.RELAY
        )
        blockchain_networks = {self.blockchain_network.network_num: self.blockchain_network}

        fetch_account_model_mock.return_value = None
        fetch_blockchain_networks_mock.return_value = blockchain_networks
        get_argument_parser_mock.return_value = argparse.ArgumentParser()
        parse_arguments_mock.return_value = self.opts
        node_runner._init_ssl_service = MagicMock()
        node_runner.run_node(
            "", self.opts, get_mock_node, NodeType.RELAY, node_init_tasks=None
        )
        self.assertEqual(self.opts.blockchain_networks, blockchain_networks)
        self.assertEqual(self.event_loop_mock.run_count, 1)

    def test_switch_to_cert_with_account(self):
        node_ssl_service = node_runner._init_ssl_service(
            NodeType.EXTERNAL_GATEWAY,
            self.opts.ca_cert_url,
            self.opts.private_ssl_base_url,
            self.opts.data_dir
        )
        node_ssl_service_with_account = node_runner._init_ssl_service(
            NodeType.EXTERNAL_GATEWAY,
            self.opts.ca_cert_url,
            os.path.join(self.opts.private_ssl_base_url, "external_gateway_account_foo"),
            self.opts.data_dir
        )
        self.assertTrue(node_ssl_service.should_renew_node_certificate())
        self.assertTrue(node_ssl_service_with_account.should_renew_node_certificate())
