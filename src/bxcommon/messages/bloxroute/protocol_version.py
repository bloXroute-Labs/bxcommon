PROTOCOL_VERSION = 19

BDN_PERFORMANCE_IGNORE_SEEN = 18
BDN_PERFORMANCE_MULTI_NODE = 17
BDN_PERFORMANCE_NEW_BLOCK = 15

RELAY_BLOCK_CAN_SEND_COMPRESSED_BLOCK_TXS_MESSAGE = 13
RELAY_BLOCK_CAN_SEND_TXS_MESSAGE = 12

# PROTOCOL_VERSION 19 (11/18/2020)
# add tx_sent_to_node and duplicate_tx_from_node to BDN performance message
#
# PROTOCOL_VERSION 18 (11/16/2020)
# support additional transaction flag
#
# PROTOCOL_VERSION 17 (10/27/2020)
# support multi-node BDN performance message
#
# PROTOCOL_VERSION 16 (10/15/2020)
# add transaction flag to TxMessage
#
# PROTOCOL_VERSION 15 (9/22/2020)
# add new_block_messages and new_block_announcements to BDN performance messages
#
# PROTOCOL VERSION 14 (9/6/2020)
# Pong(Ping Response contains additional timestamp)
#
# PROTOCOL_VERSION 12 (8/6/2020)
# relay block can send txs_message to gateways
#
# PROTOCOL_VERSION 11 (7/17/2020)
# add memory utilization to BDN performance stats message
#
# PROTOCOL_VERSION 10 (6/8/2020)
# change maximum transaction count in BDN performance stats message
#
# PROTOCOL_VERSION 9 (4/17/2020)
# add broadcast_type to broadcast messages
#
# PROTOCOL_VERSION 8 (2/5/2020)
# add timestamp to tx message types
#
# PROTOCOL_VERSION 7
# added TxQuotaFlag to transaction messages
#
#
# Copy the following template for each protocol version update:
# PROTOCOL_VERSION {N} (MM/DD/YYYY)
# brief description of the changes
