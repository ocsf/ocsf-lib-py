"""An OCSF compiler for generating OCSF schemas from source files.

Example:
    from ocsf.repository import read_repo
    from ocsf.compile import Compilation
    compilation = Compilation(read_repo("path/to/repo"))
    schema = compilation.build()

"""

from typing import Optional

from ocsf.repository import RepoPath, Repository
from ocsf.schema import OcsfSchema

from .merge import MergeResult
from .options import CompilationOptions
from .planners.annotations import AnnotationPlanner
from .planners.category_events import MapEventToCategoryPlanner
from .planners.datetime import DateTimePlanner
from .planners.dictionary import DictionaryPlanner
from .planners.extends import ExtendsPlanner
from .planners.extension import (
    ExtensionCopyPlanner,
    ExtensionMergePlanner,
    ExtensionPrefixPlanner,
    MarkExtensionPlanner,
)
from .planners.include import IncludePlanner
from .planners.object_type import ObjectTypePlanner
from .planners.observable import BuildObservableTypesPlanner, MarkObservablesPlanner
from .planners.planner import Operation, Planner
from .planners.profile import ExcludeProfileAttrsPlanner, MarkProfilePlanner
from .planners.set_category import SetCategoryPlanner
from .planners.uid import UidPlanner
from .planners.uid_names import UidSiblingPlanner
from .protoschema import ProtoSchema

FileOperations = dict[RepoPath, list[Operation]]
CompilationOperations = list[FileOperations]
CompilationPlan = list[Operation]

FileMutations = list[tuple[Operation, MergeResult]]
CompilationMutations = dict[RepoPath, FileMutations]
PlanningPhase = list[Planner]


class Compilation:
    def __init__(self, repo: Repository, options: CompilationOptions | None = None):
        self._operations: Optional[CompilationOperations] = None
        self._plan: Optional[CompilationPlan] = None
        self._mutations: Optional[CompilationMutations] = None
        self._schema: Optional[OcsfSchema] = None
        self._repo = repo
        self._proto = ProtoSchema(repo)
        _options = CompilationOptions() if options is None else options

        # The arrangement of planners to phases is very important. If you think
        # it needs to change, you're probably wrong.
        self._planners: list[PlanningPhase] = [
            [
                # Expand annotations in profiles and includes.
                AnnotationPlanner(self._proto, _options),
                # Set the extension property of objects and events introduced to
                # core by extensions.
                MarkExtensionPlanner(self._proto, _options),
                # Set the profile name of attributes to the profile that adds
                # them to the object or event.
                MarkProfilePlanner(self._proto, _options),
                # Process $include directives.
                IncludePlanner(self._proto, _options),
                # Process extends directives.
                ExtendsPlanner(self._proto, _options),
                # Build the observable type_id enum based on values found across
                # the schema.
                BuildObservableTypesPlanner(self._proto, _options),
                # Process definitions in extensions that modify records in core
                # (reverse extends?).
                ExtensionMergePlanner(self._proto, _options),
                # Remove attributes from deactivated profiles.
                ExcludeProfileAttrsPlanner(self._proto, _options),
            ],
            [
                # Set the category of events.
                # TODO: Can this be performed in the prior phase?
                SetCategoryPlanner(self._proto, _options),
            ],
            [
                # Build the UID enumerations (type_id, class_uid, etc.).
                UidPlanner(self._proto, _options),
                # Complete missing attribute details using dictionary.json.
                DictionaryPlanner(self._proto, _options),
            ],
            [
                # Prefix the names of objects and events added by extensions
                # with their extension name, and also update all attribute type
                # references to them. Only performed if
                # options.prefix_extensions is True.
                ExtensionPrefixPlanner(self._proto, _options),
                # For attributes with object types, change type to object and
                # populate the object_type and object_name properties to match
                # the output of the OCSF server. Only performed if
                # options.set_object_types is True.
                ObjectTypePlanner(self._proto, _options),
                # Build the sibling _name fields for UID enumerations.
                UidSiblingPlanner(self._proto, _options),
                # Apply the datetime synthetic profile.
                DateTimePlanner(self._proto, _options),
                # Set the observable property of attributes to the corresponding
                # observable.type_id value to make building the observables
                # attribute of records easier. Only performed if
                # options.set_observable is True.
                MarkObservablesPlanner(self._proto, _options),
                # Map events to the `classes` dictionary of each category.
                MapEventToCategoryPlanner(self._proto, _options),
                # Copy records that are ONLY defined in extensions to the core
                # schema so that they are included by ProtoSchema.schema().
                ExtensionCopyPlanner(self._proto, _options),
            ],
        ]

    def analyze(self) -> CompilationOperations:
        """Identify the operations needed to compile the schema.

        Returns:
            A list of dictionaries, where each dictionary maps a file path to a
            list of operations, and the list index corresponds to a phase of
            compilation.
        """
        operations: CompilationOperations = []
        for phase in self._planners:
            found: FileOperations = {}
            for planner in phase:
                for file in self._repo.files():
                    ops = planner.analyze(file)
                    if ops is not None:
                        if isinstance(ops, Operation):
                            ops = [ops]

                        for op in ops:
                            if op.target not in found:
                                found[op.target] = []
                            found[op.target].append(op)

            operations.append(found)

        self._operations = operations
        return operations

    def order(self, operations: Optional[CompilationOperations] = None) -> CompilationPlan:
        """Order the operations for compilation.

        Returns:
            A list of operations in the order they should be applied.
        """
        if operations is not None:
            self._operations = operations

        if self._operations is None:
            self.analyze()
            assert self._operations is not None

        plan: CompilationPlan = []

        def follow(path: RepoPath, phase: FileOperations, planned: set[RepoPath]):
            if path in planned or path not in phase:
                return
            planned.add(path)
            for op in phase[path]:
                if op.prerequisite is not None and op.prerequisite not in planned:
                    follow(op.prerequisite, phase, planned)
                plan.append(op)

        for phase in self._operations:
            planned: set[RepoPath] = set()
            for path, _ in phase.items():
                follow(path, phase, planned)

        self._plan = plan
        return plan

    def compile(self, plan: Optional[CompilationPlan] = None) -> CompilationMutations:
        """Applies all operations in the plan to the schema.

        Returns:
            A dictionary of file paths to lists of tuples, where each tuple
            contains the operation that was applied and the fields modified by
            the operation.
        """
        if plan is not None:
            self._plan = plan

        if self._plan is None:
            self.order()
            assert self._plan is not None

        mutations: CompilationMutations = {}
        for op in self._plan:
            if op.target not in mutations:
                mutations[op.target] = []
            result = op.apply(self._proto)
            mutations[op.target].append((op, result))

        self._mutations = mutations
        return mutations

    def build(self) -> OcsfSchema:
        """Return a compiled schema."""
        if self._mutations is None:
            self.compile()
            assert self._mutations is not None

        if self._schema is None:
            self._schema = self._proto.schema()

        return self._schema
