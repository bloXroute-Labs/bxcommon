from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.validation.message_validation_error import MessageValidationError


class ControlFlagValidationError(MessageValidationError):
    is_cancelled_cut_through: bool

    def __init__(self, msg: str, control_flag_byte: int) -> None:
        super(ControlFlagValidationError, self).__init__(msg)
        if BloxrouteMessageControlFlags(control_flag_byte) is BloxrouteMessageControlFlags.NONE:
            self.is_cancelled_cut_through = True
        else:
            self.is_cancelled_cut_through = False
