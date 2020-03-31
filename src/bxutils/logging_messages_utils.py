from dataclasses import dataclass
from typing import Optional


@dataclass
class LogMessage:
    code: Optional[str]
    category: Optional[str]
    text: str


logger_names = set(["bxcommon"])
