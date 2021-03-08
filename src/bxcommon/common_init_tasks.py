import sys

from bxcommon.common_opts import CommonOpts
from bxcommon.services import sdn_http_service
from bxcommon.utils import cli, model_loader, node_cache
from bxcommon.models.node_model import NodeModel

from bxutils.ssl import ssl_serializer
from bxutils.ssl.ssl_certificate_type import SSLCertificateType
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils import logging


logger = logging.get_logger(__name__)


def _register_node(opts: CommonOpts, node_ssl_service: NodeSSLService) -> NodeModel:
    temp_node_model = model_loader.load_model(NodeModel, opts.__dict__)
    if node_ssl_service.should_renew_node_certificate():
        temp_node_model.csr = ssl_serializer.serialize_csr(
            node_ssl_service.create_csr()
        )

    try:
        node_model = sdn_http_service.register_node(temp_node_model)
    except ValueError as e:
        logger.fatal(e)
        sys.exit(1)
    except EnvironmentError as e:
        logger.info(
            "Unable to contact SDN to register node using {}, attempting to get information from cache",
            opts.sdn_url,
        )

        cache_info = node_cache.read(opts)
        if not cache_info or not cache_info.node_model:
            logger.fatal(
                "Unable to reach the SDN and no local cache information was found. Unable to start the node"
            )
            sys.exit(1)
        node_model = cache_info.node_model

    if node_model.should_update_source_version:
        logger.info(
            "UPDATE AVAILABLE! An updated software version is available, please download and install the "
            "latest version"
        )

    return node_model


def set_network_info(opts: CommonOpts, _node_ssl_service) -> None:
    cli.set_blockchain_networks_info(opts)
    cli.parse_blockchain_opts(opts, opts.node_type)


def set_node_model(opts: CommonOpts, node_ssl_service) -> None:
    """
    Must be executed after set_network_info
    :param self:
    :param opts:
    :param node_ssl_service:
    :return:
    """
    node_model = None
    if opts.node_id:
        # Test network, get pre-configured peers from the SDN.
        node_model = sdn_http_service.fetch_node_attributes(opts.node_id)

    if not node_model:
        node_model = _register_node(opts, node_ssl_service)

    if node_model.cert is not None:
        private_cert = ssl_serializer.deserialize_cert(node_model.cert)
        node_ssl_service.blocking_store_node_certificate(private_cert)
        ssl_context = node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)
        sdn_http_service.reset_pool(ssl_context)

    # Add opts from SDN, but don't overwrite CLI args
    default_values_to_update = [None, -1]
    for key, val in node_model.__dict__.items():
        if opts.__dict__.get(key) in default_values_to_update:
            opts.__dict__[key] = val


init_tasks = [
    set_network_info,
    set_node_model,
]
