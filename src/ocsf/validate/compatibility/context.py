from dataclasses import dataclass

from ocsf.compare import ChangedSchema
from ocsf.schema import OcsfSchema


@dataclass
class CompatibilityContext:
    change: ChangedSchema
    before: OcsfSchema
    after: OcsfSchema
