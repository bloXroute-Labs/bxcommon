from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

logger_filters = logging.get_logger(LogRecordType.TransactionFiltering, __name__)


def reformat_tx_value(value: str) -> float:
    return float(int(value, 0))


def reformat_address(address: str) -> str:
    # eth allows 0x in the `to` when a new contract was created. In this case we pad the 0
    # the issue is in th pycond that search strings as substring and not exact
    if address == "0x":
        return "0x0000000000000000000000000000000000000000"
    return address.lower()


def reformat_gas_price(value: str) -> int:
    return int(value, 0)


def reformat_input_to_method_id(input_field: str) -> str:
    if len(input_field) >= 10:
        return input_field[2:10]
    return ""
