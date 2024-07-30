from dataclasses import dataclass

from ..protoschema import ProtoSchema
from ..merge import MergeResult, merge
from .planner import Operation, Planner, Analysis
from ocsf.repository import (
    DefinitionFile,
    CategoryDefn,
    EnumMemberDefn,
    CategoriesDefn,
    EventDefn,
    SpecialFiles,
    as_path,
    RepoPaths,
    ExtensionDefn,
    AttrDefn,
    AnyDefinition,
)


def _find_extn_path(schema: ProtoSchema, target: str) -> str | None:
    for extn_dir in schema.repo.extensions():
        if extn_dir == target:
            return extn_dir

        extn = schema[as_path(RepoPaths.EXTENSIONS, extn_dir, SpecialFiles.EXTENSION)]
        assert isinstance(extn.data, ExtensionDefn)
        if extn.data.name == target:
            return extn_dir

    return None


@dataclass(eq=True, frozen=True)
class UidOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        file = schema[self.target]
        defn = file.data
        assert defn is not None
        assert isinstance(defn, EventDefn)

        enums = EventDefn()
        enums.attributes = {}

        # Find the Extension UID, if there is one
        extn_uid = 0
        if defn.src_extension is not None:
            # look up extn uid
            extn_dir = _find_extn_path(schema, defn.src_extension)
            if extn_dir is None:
                raise ValueError(f"Extension {defn.src_extension} not found for {self.target}")

            extn = schema[as_path(RepoPaths.EXTENSIONS, extn_dir, SpecialFiles.EXTENSION)]
            assert isinstance(extn.data, ExtensionDefn)
            if extn.data.uid is not None:
                extn_uid = extn.data.uid

        # Find the category UID and build the category_uid enum
        cat_uid = 0
        if defn.category is not None:
            cats = schema[as_path(SpecialFiles.CATEGORIES)].data
            assert isinstance(cats, CategoriesDefn)
            if cats.attributes is None:
                return []

            cat = cats.attributes.get(defn.category, None)
            if isinstance(cat, CategoryDefn):
                assert cat.uid is not None
                cat_uid = cat.uid

                enums.attributes["category_uid"] = AttrDefn(
                    enum={str(cat_uid): EnumMemberDefn(caption=cat.caption, description=cat.description)}
                )

        # Calculate the Class UID and build the class_uid enum
        if defn.uid is not None:
            class_uid = (extn_uid * 100000) + (cat_uid * 1000) + defn.uid
            enums.uid = class_uid
        else:
            class_uid = 0
            if defn.name == "base_event":
                enums.uid = 0

        attr = AttrDefn()
        attr.enum = {}
        attr.enum[str(class_uid)] = EnumMemberDefn(caption=defn.caption, description=defn.description)
        enums.attributes["class_uid"] = attr

        # Build Activity IDs and the Activity ID enum
        if (
            isinstance(defn.attributes, dict)
            and "activity_id" in defn.attributes
            and isinstance(defn.attributes["activity_id"], AttrDefn)
            and defn.attributes["activity_id"].enum is not None
        ):
            attr = AttrDefn()
            attr.enum = {}

            for key, value in defn.attributes["activity_id"].enum.items():
                type_uid = (class_uid * 100) + int(key)
                attr.enum[str(type_uid)] = EnumMemberDefn(
                    caption=f"{defn.caption}: {value.caption}", description=value.description
                )

            enums.attributes["type_uid"] = attr

        # Remove any enum members that were inherited from base_event
        if defn.name != "base_event":
            if (
                isinstance(defn.attributes, dict)
                and "class_uid" in defn.attributes
                and isinstance(defn.attributes["class_uid"], AttrDefn)
            ):
                defn.attributes["class_uid"].enum = {}
            if (
                isinstance(defn.attributes, dict)
                and "category_uid" in defn.attributes
                and isinstance(defn.attributes["category_uid"], AttrDefn)
            ):
                defn.attributes["category_uid"].enum = {}
            if (
                isinstance(defn.attributes, dict)
                and "type_uid" in defn.attributes
                and isinstance(defn.attributes["type_uid"], AttrDefn)
            ):
                defn.attributes["type_uid"].enum = {}

        return merge(
            defn,
            enums,
            overwrite=True,
            allowed_fields=[
                ("uid",),
                ("attributes", "category_uid"),
                ("attributes", "class_uid"),
                ("attributes", "type_uid"),
            ],
        )

    def __str__(self):
        return f"UIDs for {self.target}"


class UidPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if isinstance(input.data, EventDefn):
            return UidOp(input.path, SpecialFiles.CATEGORIES)
