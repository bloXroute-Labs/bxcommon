from bxutils import log_messages
from bxutils.log_message_categories import LogMessageCategories

categories_map = {
    log_messages.EMPTY_BLOCKCHAIN_NETWORK_LIST:  LogMessageCategories.EMPTY_VALUE_FROM_CALL,
    log_messages.READ_CACHE_FILE_ERROR: LogMessageCategories.LOCAL_IO_ERROR
}