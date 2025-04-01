from ocsf.compare import ChangedSchema
from ocsf.schema import OcsfSchema, OcsfType
from ocsf.validate.compatibility import CompatibilityContext

types = {
    "string_t": OcsfType(caption="String", type="string_t"),
    "file_path_t": OcsfType(caption="File Path", type="string_t"),
}


def get_context(s: ChangedSchema):
    return CompatibilityContext(
        change=s,
        before=OcsfSchema("1.0.0", types=types),
        after=OcsfSchema("1.0.1", types=types),
    )
