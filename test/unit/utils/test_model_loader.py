import json
import unittest

from bxcommon.connections.node_type import NodeType
from bxcommon.models.node_model import NodeModel
from bxcommon.utils import model_loader


class TestModelLoader(unittest.TestCase):

    def test_should_not_load_future_attributes(self):

        future_node = {
            "node_type": NodeType.RELAY,
            "external_ip": "foo",
            "external_port": 123,
            "garbage_attribute": "Test"
        }

        current_version_node = model_loader.load(NodeModel, future_node)
        self.assertEqual(False, hasattr(current_version_node, "garbage_attribute"))
        self.assertEqual(True, hasattr(current_version_node, "node_type"))
        self.assertEqual(True, hasattr(current_version_node, "external_ip"))
        self.assertEqual(True, hasattr(current_version_node, "external_port"))
