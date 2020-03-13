from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.validation.message_validation_error import MessageValidationError


class ControlFlagValidationError(MessageValidationError):
    def __init__(self, msg: str, control_flag_byte: int = None):
        super(ControlFlagValidationError, self).__init__(msg)
        self.is_cancelled_cut_through = BloxrouteMessageControlFlags.NONE is BloxrouteMessageControlFlags(control_flag_byte)

