from typing import List, Optional
from abc import ABC, abstractmethod

from bxcommon.common_opts import CommonOpts
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils import logging

logger = logging.get_logger(__name__)

DEFAULT_TASK_ORDER = 100
OptsType = CommonOpts


class AbstractInitTask(ABC):
    done: bool
    requires: List["AbstractInitTask"]
    order: int
    name: str

    def __init__(
        self,
        *requires: "AbstractInitTask",
        order: int = DEFAULT_TASK_ORDER,
        name: Optional[str] = None,
    ) -> None:
        self.done = False
        self.requires = list(requires)
        self.order = order
        self.name = name or str(self.__class__.__name__)

    def __call__(self, opts: OptsType, node_ssl_service: NodeSSLService) -> bool:
        if not self.done:
            if not all(
                task(opts=opts, node_ssl_service=node_ssl_service)
                for task in self.requires
            ):
                return False
            logger.trace("Running Init Task {} {}", self.name, self.order)
            self.action(opts, node_ssl_service)
            self.done = True
        return self.done

    @abstractmethod
    def action(self, opts: OptsType, node_ssl_service: NodeSSLService) -> None:
        pass
