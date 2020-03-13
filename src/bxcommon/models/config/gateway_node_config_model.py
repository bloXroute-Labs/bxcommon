#TODO: This file is duplicated in bxapi. Keep in sync until we have a long term solution to make one
# of them obsolete.

from dataclasses import dataclass

from bxcommon.models.config.abstract_config_model import AbstractConfigModel
from bxcommon.models.config.cron_config_model import CronConfigModel
from bxcommon.models.config.log_config_model import LogConfigModel
from bxcommon.models.config.stats_config_model import StatsConfigModel


@dataclass
class GatewayNodeConfigModel(AbstractConfigModel):
    log_config: LogConfigModel = None
    stats_config: StatsConfigModel = None
    cron_config: CronConfigModel = None



