

ProtoSchema:
  resolve locations to files
  maintain copies of WIP definitions
  DON'T resolve(Location) -> Location - this is not 1:1, plus it's awkward

Step:
  Identifies and applies operations
  analyze() -> Op
  apply() -> MergeResult

CompilationOptions:
  profile order - list of profiles in order

Compilation:
  collection of steps
  analyze() ->
    Scans repo, assemble list of steps as [phase: {Location: List[Op]}]
  compile() ->
    Apply changes
    List of [phase: {Location: List[Tuple[Op, MergeResult]]}]
  schema() -> OcsfSchema


FileLocation - objects/thing.json
ObjectLocation - thing


### Phase 1
Defns in Extension:
  if extension is enabled:
    if record name exists in core, merge
    else, copy to core

Include:
  merge target file to subject file

Profile:
  REMOVE attributes if the profile isn't enabled

Extends
  merge target record to subject record

### Phase 2
Dictionary
  merge all missing attributes from dictionary.json to subject

### Phase 3
Observable

Category ID

Class ID

Type ID

### Phase 4
Copy to schema