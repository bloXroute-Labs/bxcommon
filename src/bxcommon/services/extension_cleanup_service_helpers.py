from datetime import datetime
import time
import typing

from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

from bxcommon.utils.proxy import task_pool_proxy
from bxcommon.services.transaction_service import TransactionService
from bxcommon.services.extension_transaction_service import ExtensionTransactionService
from bxcommon.messages.bloxroute.abstract_cleanup_message import AbstractCleanupMessage


import task_pool_executor as tpe   # pyre-ignore for now, figure this out later (stub file or Python wrapper?)

logger = logging.get_logger(LogRecordType.TransactionCleanup, __name__)
logger_memory_cleanup = logging.get_logger(LogRecordType.BlockCleanup, __name__)

def contents_cleanup(transaction_service: TransactionService,
                     block_confirmation_message: AbstractCleanupMessage,
                     cleanup_tasks
                     ):
    start_datetime = datetime.utcnow()
    start_time = time.time()
    tx_service = typing.cast(ExtensionTransactionService, transaction_service)
    cleanup_task = cleanup_tasks.borrow_task()
    cleanup_task.init(tpe.InputBytes(block_confirmation_message.buf), tx_service.proxy)

    tx_before_cleanup = transaction_service.get_tx_hash_to_contents_len()
    short_id_count_before_cleanup = transaction_service.get_short_id_count()

    task_pool_proxy.run_task(cleanup_task)
    tx_after_cleanup = transaction_service.get_tx_hash_to_contents_len()
    short_id_count_after_cleanup = transaction_service.get_short_id_count()

    short_ids = cleanup_task.short_ids()
    total_content_removed = cleanup_task.total_content_removed()

    tx_count = cleanup_task.tx_count()
    message_hash = block_confirmation_message.message_hash()
    tx_service.update_removed_transactions(total_content_removed, short_ids)
    transaction_service.on_block_cleaned_up(message_hash)
    end_datetime = datetime.utcnow()
    end_time = time.time()
    duration = end_time - start_time
    logger_memory_cleanup.statistics(

        {
            "type": "BlockTransactionsCleanup",
            "block_hash": repr(message_hash),
            "block_transactions_count": block_confirmation_message._tx_hashes_count + block_confirmation_message._sids_count,
            "tx_hash_to_contents_len_before_cleanup": tx_before_cleanup,
            "tx_hash_to_contents_len_after_cleanup": tx_after_cleanup,
            "short_id_count_before_cleanup": short_id_count_before_cleanup,
            "short_id_count_after_cleanup": short_id_count_after_cleanup,
            "cleanup_mechanism": "block_confirmation_message_received",
        }
    )
    logger.statistics(
        {
            "type": "MemoryCleanup",
            "event": "CacheStateAfterBlockCleanup",
            "data": transaction_service.get_cache_state_json(),
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "duration": duration,
            "total_content_removed": total_content_removed,
            "tx_count": tx_count,
            "short_ids_count": len(short_ids),
            "message_hash": repr(message_hash),
        }
    )
    cleanup_tasks.return_task(cleanup_task)
