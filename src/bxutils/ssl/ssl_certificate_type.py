from enum import Enum


class SSLCertificateType(Enum):
    CA = 1
    REGISTRATION_ONLY = 2
    PRIVATE = 3
