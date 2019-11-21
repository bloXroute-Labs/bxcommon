import unittest

from bxutils.logging import log_config

from bxcommon.utils import model_loader
from bxcommon.models.node_model import NodeModel
from bxcommon.connections.node_type import NodeType
from bxcommon import constants


class TestNodeModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        log_config.create_logger(None)

    def test_from_json(self):
        node_json = {
            "external_ip": "foo",
            "external_port": 123,
            "network": "bad_net_name",
            "node_type": "RELAY"
        }
        node = model_loader.load_model(NodeModel, node_json)

        self.assertEqual(node_json.get("external_ip"), node.external_ip)
        self.assertEqual(node_json.get("external_port"), node.external_port)
        self.assertEqual(node_json.get("network"), node.network)
        self.assertEqual(NodeType.RELAY, node.node_type)

    def test_invalid_json(self):
        node_json = {
            "a": "foo",
            "b": "bazz",
            "node_type": "garbage"
        }

        # Should throw error, none of the keys are right, node_type is wrong
        with self.assertRaises(TypeError):
            model_loader.load_model(NodeModel, node_json)

    def test_add_new_gateway_continent(self):
        node_json = {
            "external_ip": "foo",
            "external_port": 123,
            "network": constants.DEFAULT_NETWORK_NAME,
            "node_type": "RELAY",
            "continent": "AT"
        }
        node = model_loader.load_model(NodeModel, node_json)
        self.assertEqual(node.continent, None, "Continent AT should changed to None")

        node_json = {
            "external_ip": "foo",
            "external_port": 123,
            "network": constants.DEFAULT_NETWORK_NAME,
            "node_type": "RELAY",
            "continent": "EU"
        }
        node = model_loader.load_model(NodeModel, node_json)
        self.assertEqual(node.continent, "EU", "Continent EU should remains")

    def test_add_new_gateway_country(self):
        node_json = {
            "external_ip": "foo",
            "external_port": 123,
            "network": constants.DEFAULT_NETWORK_NAME,
            "country": "United States",
            "node_type": "RELAY"
        }
        node = model_loader.load_model(NodeModel, node_json)
        self.assertEqual(node.country, "United States", "country United States should remains")

        node_json = {
            "external_ip": "foo",
            "external_port": 123,
            "network": constants.DEFAULT_NETWORK_NAME,
            "node_type": "RELAY",
            "country": "Country name after truncation. Very long country that has more than 30 characters"
        }
        node = model_loader.load_model(NodeModel, node_json)
        self.assertEqual(node.country, "Country name after truncation.", "country name should be truncated")
