from enum import Enum


class LogMessageCategories (Enum):
    FATAL_ERROR = "Fatal Error"
    NO_PEERS = "No peers"
    EMPTY_VALUE_FROM_CALL = "Empty value from call"
    LOCAL_IO_ERROR = "Local IO Error"
    UNHEALTHY_CONN = "Unhealthy connection"
    UNCATEGORIZED = "Uncategorized"
