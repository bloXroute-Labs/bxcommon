from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.node_model import NodeModel

ALL_NODE_KEYS = NodeModel().__dict__

ALL_BLOCKCHAIN_NETWORK_KEYS = BlockchainNetworkModel(None, None, None).__dict__


def load_node_model(model_params):
    """
    NOTE: This is the same model loader that is used in BXAPI - any changes made here should also be made there

    Ensures models are forward compatible - if attributes are added to models in future versions and these models saved
    to Redis, this function ensures that only the attributes that the current version knows about are loaded
    :param model_params: Attributes from the retrieved model to load
    :return: Dict of attributes with which to create the model
    """
    return {key: model_params[key] for key in ALL_NODE_KEYS if key in model_params}


def load_blockchain_network_model(model_params):
    """
    NOTE: This is the same model loader that is used in BXAPI - any changes made here should also be made there

    Ensures models are forward compatible - if attributes are added to models in future versions and these models saved
    to Redis, this function ensures that only the attributes that the current version knows about are loaded
    :param model_params: Attributes from the retrieved model to load
    :return: Dict of attributes with which to create the model
    """
    return {key: model_params[key] for key in ALL_BLOCKCHAIN_NETWORK_KEYS if key in model_params}
