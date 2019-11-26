from dataclasses import dataclass
from bxutils.logging.status.analysis import Analysis
from bxutils.logging.status.summary import Summary


@dataclass
class Diagnostics:
    summary: Summary
    analysis: Analysis
