import unittest

from mock import mock

from bxcommon.connections.node_type import NodeType
from bxcommon.services import sdn_http_service


class TestSdnHttpService(unittest.TestCase):

    def test_fetch_config(self):
        with mock.patch.object(sdn_http_service.http_service, "get_json") as mock_http_service, mock.patch.object(
                sdn_http_service.logger, "debug"):
            mock_node = {
                "node_id": "aaa",
                "node_type": NodeType.RELAY,
                "external_ip": "foo",
                "external_port": 123,
                "garbage_attr": "garbage"
            }

            mock_http_service.return_value = mock_node

            loaded_node = sdn_http_service.fetch_node_attributes("aaa")

            self.assertEqual("aaa", loaded_node.node_id)


    def test_fetch_blockchain_network(self):
        with mock.patch.object(sdn_http_service.http_service, "get_json") as mock_http_service:
            mock_bc_network = {
                "protocol": "bar",
                "network": "foo",
                "network_num": "999",
            }

            mock_http_service.return_value = mock_bc_network

            blockchain_network = sdn_http_service.fetch_blockchain_network("bar", "foo")

            self.assertEqual("999", blockchain_network.network_num)

    def test_fetch_blockchain_networks(self):
        with mock.patch.object(sdn_http_service.http_service, "get_json") as mock_http_service:
            mock_bc_network_a = {
                "protocol": "bar1",
                "network": "foo1",
                "network_num": "999",
            }

            mock_bc_network_b = {
                "protocol": "bar2",
                "network": "foo2",
                "network_num": "222",
            }

            mock_http_service.return_value = [mock_bc_network_a, mock_bc_network_b]

            blockchain_networks = sdn_http_service.fetch_blockchain_networks()

            self.assertEqual(2, len(blockchain_networks))
            self.assertEqual("999", blockchain_networks[0].network_num)
            self.assertEqual("222", blockchain_networks[1].network_num)
