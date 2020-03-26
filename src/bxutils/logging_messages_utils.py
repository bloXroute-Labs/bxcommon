from dataclasses import dataclass


@dataclass
class LogMessage:
    code: str
    category: str
    text: str


logger_names = set(["bxcommon"])


