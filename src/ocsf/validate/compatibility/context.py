from dataclasses import dataclass
from ocsf.schema import OcsfSchema
from ocsf.compare import ChangedSchema


@dataclass
class CompatibilityContext:
    change: ChangedSchema
    before: OcsfSchema
    after: OcsfSchema
