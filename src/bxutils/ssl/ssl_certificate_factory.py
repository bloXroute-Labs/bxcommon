import functools
import os
import ssl
import typing
import urllib.request
import urllib.response
from asyncio import Transport
from datetime import datetime, time, date
from ssl import SSLSocket
from typing import Callable, Iterable, Union, IO

from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization, \
    EllipticCurvePrivateKey
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509 import Certificate, CertificateSigningRequest, \
    CertificateSigningRequestBuilder, SubjectAlternativeName, ExtensionNotFound, \
    CertificateBuilder, AuthorityKeyIdentifier
from cryptography.x509.extensions import KeyUsage, UnrecognizedExtension, BasicConstraints
# pyre-fixme[21]: Could not find `loop`.
from uvloop.loop import TCPTransport  

from bxutils import constants
from bxutils.ssl import ssl_serializer

KEY_FILE_FORMAT = constants.SSL_KEY_FILE_FORMAT
CERT_FILE_FORMAT = constants.SSL_CERT_FILE_FORMAT


def create_csr(key: EllipticCurvePrivateKey, template_cert: Certificate) -> CertificateSigningRequest:
    """
    Create a Certificate Signing Request (CSR)
    matching to a corresponding template_cert and sign it with a private key.
    :param key: the private key to sign the CSR
    :param template_cert: a template for retrieving the subject information.
    :return: CSR (https://en.wikipedia.org/wiki/Certificate_signing_request)
    """
    csr_builder = CertificateSigningRequestBuilder().subject_name(
        template_cert.subject
    )
    try:
        subject_alt_name = template_cert.extensions.get_extension_for_class(SubjectAlternativeName)
        csr_builder = csr_builder.add_extension(
            subject_alt_name.value,
            critical=False
        )
    except ExtensionNotFound:
        pass

    return csr_builder.sign(key, SHA256(), backends.default_backend())


def generate_key() -> EllipticCurvePrivateKeyWithSerialization:
    """
    Generate an EC (https://en.wikipedia.org/wiki/Elliptic-curve_cryptography) private key
    to be used for signing an SSL certificate or CSR.
    :return: EC private key
    """
    return ec.generate_private_key(ec.SECP384R1(), backends.default_backend())


def store(
        path: str,
        data: bytes,
        stream_factory: Callable[[str], IO] = functools.partial(open, mode="wb")
) -> None:
    """
    Stores raw certificate data (in PEM format)
    :param path: the file path in which the data will be written to.
    :param data: the PEM encoded certificate data
    :param stream_factory: a handler callback to open a file stream (to make this method more testable)
    """
    with stream_factory(path) as stream:
        stream.write(data)


def store_key(
        key: EllipticCurvePrivateKeyWithSerialization,
        folder_path: str,
        name: str,
        stream_factory: Callable[[str], IO] = functools.partial(open, mode="wb")
) -> str:
    """
    Stores an EC private key.
    :param key: the private key to store
    :param folder_path: the ssl folder path
    :param name: the name prefix for the key file (see: KEY_FILE_FORMAT)
    :param stream_factory: a handler callback to open a file stream (to make this method more testable)
    :return: the full path of the key file
    """
    file_path = os.path.join(folder_path, KEY_FILE_FORMAT.format(name))
    store(
        file_path,
        ssl_serializer.serialize_key(key).encode("utf-8"),
        stream_factory
    )
    return file_path


def store_certificate(
        cert: Certificate,
        folder_path: str,
        name: str,
        stream_factory: Callable[[str], IO] = functools.partial(open, mode="wb")
) -> str:
    """
    Stores an SSL certificate.
    :param cert: the certificate to store
    :param folder_path: the ssl folder path
    :param name: the name prefix for the certificate file (see: CERT_FILE_FORMAT)
    :param stream_factory: a handler callback to open a file stream (to make this method more testable)
    :return: the full path of the certificate file
    """
    file_path = os.path.join(folder_path, CERT_FILE_FORMAT.format(name))
    store(
        file_path,
        ssl_serializer.serialize_cert(cert).encode("utf-8"),
        stream_factory
    )
    return file_path


def fetch_file(url: str) -> IO:
    """
    Fetch a PEM encoded file from a URL.
    :param url: the file URL
    :return: stream like object
    """
    return urllib.request.urlopen(url)


def fetch_cert(url: str) -> Certificate:
    """
    Fetch a certificate from a URL.
    :param url: the URL to the certificate file
    :return: a certificate object
    """
    with fetch_file(url) as cert_file:
        return ssl_serializer.deserialize_cert(cert_file.read())


def fetch_key(url: str) -> EllipticCurvePrivateKeyWithSerialization:
    """
    Fetch a private key from a URL.
    :param url: the URL to the private key file
    :return: a private key object
    """
    with fetch_file(url) as key_file:
        return ssl_serializer.deserialize_key(key_file.read())


def get_socket_cert(ssl_socket: Union[SSLSocket, ssl.SSLObject]) -> Certificate:
    """
    Obtain a peer certificate from an SSL socket.
    :param ssl_socket: the SSL socket object
    :return: a certificate object
    """
    der_cert = ssl_socket.getpeercert(True)
    pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)  # pyre-ignore
    return ssl_serializer.deserialize_cert(pem_cert)


# pyre-fixme[11]: Annotation `TCPTransport` is not defined as a type.
def get_transport_cert(transport: Union[Transport, TCPTransport]) -> Certificate:
    """
    Obtain a peer certificate from a Transport socket wrapper
    :param transport: the SSL socket transport wrapper
    :return: a certificate object
    :raise: ValueError if the transport doesn't wrap an SSL socket
    """
    ssl_socket = transport.get_extra_info("ssl_object")
    if isinstance(ssl_socket, (SSLSocket, ssl.SSLObject)):
        return get_socket_cert(ssl_socket)
    else:
        raise ValueError("transport does not wrap an ssl socket")


def sign_csr(
    csr: CertificateSigningRequest,
    ca_cert: Certificate,
    key: EllipticCurvePrivateKey,
    expiration_date: date,
    custom_extensions: Iterable[Union[KeyUsage, UnrecognizedExtension, BasicConstraints]]
) -> Certificate:
    """
    Sign a CSR with CA credentials.
    :param csr: the CSR
    :param ca_cert: the CA certificate
    :param key: the CA private key
    :param expiration_date: expiration date
    :param custom_extensions: custom extensions to be added to the certificate
    :return: a certificate object
    """
    issuer = ca_cert.subject
    now = datetime.utcnow()
    cert_builder = CertificateBuilder().issuer_name(issuer).subject_name(csr.subject).public_key(
        csr.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(now).not_valid_after(
        datetime.combine(expiration_date, time(), None)
    ).add_extension(
        extension=AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()),
        critical=False
    )
    try:
        cert_builder = cert_builder.add_extension(
            csr.extensions.get_extension_for_class(SubjectAlternativeName).value, critical=False
        )
    except ExtensionNotFound:
        pass
    for extension in custom_extensions:
        if isinstance(extension, UnrecognizedExtension):
            critical = False
        else:
            critical = True
        # pyre-fixme[6]: Expected `ExtensionType` for 1st param but got
        #  `Union[BasicConstraints, KeyUsage, UnrecognizedExtension]`.
        cert_builder = cert_builder.add_extension(extension, critical=critical)
    return cert_builder.sign(key, SHA256(), backends.default_backend())
