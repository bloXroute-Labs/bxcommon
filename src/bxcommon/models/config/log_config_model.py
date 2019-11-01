from dataclasses import dataclass, field
from typing import Dict
from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class LogConfigModel:
    log_level: str
    log_flush_immediately: bool
    log_level_overrides: Dict[str, str] = field(default_factory=dict)
