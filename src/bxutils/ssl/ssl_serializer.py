from typing import Union

from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509 import Certificate, CertificateSigningRequest


def to_binary(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        return data.encode("utf-8")
    else:
        return data


def serialize_csr(csr: CertificateSigningRequest) -> str:
    return csr.public_bytes(Encoding.PEM).decode("utf-8")


def deserialize_csr(csr: Union[str, bytes]) -> CertificateSigningRequest:
    return x509.load_pem_x509_csr(to_binary(csr), backends.default_backend())


def serialize_cert(cert: Certificate) -> str:
    return cert.public_bytes(Encoding.PEM).decode("utf-8")


def serialize_key(key: EllipticCurvePrivateKeyWithSerialization) -> str:
    return key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()).decode("utf-8")


def deserialize_cert(cert: Union[str, bytes]) -> Certificate:
    return x509.load_pem_x509_certificate(to_binary(cert), backends.default_backend())


def deserialize_key(key: Union[str, bytes]) -> EllipticCurvePrivateKeyWithSerialization:
    return serialization.load_pem_private_key(to_binary(key), None, backends.default_backend())

