from dataclasses import dataclass, field
from typing import Dict
from typing import Optional

from bxcommon.models.config.abstract_config_model import AbstractConfigModel


@dataclass
class LogConfigModel(AbstractConfigModel):
    log_level: Optional[str] = None
    log_flush_immediately: Optional[bool] = None
    log_level_overrides: Dict[str, str] = field(default_factory=dict)
