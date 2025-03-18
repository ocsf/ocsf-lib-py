# Schema Cache for ocsf-lib-py

This directory contains cached copies of the "compiled" OCSF schema. This is
used primarily to reduce requests to the OCSF Server, especially for
backwards-compatibility validation.

To add a schema to this cache, checkout the version of the OCSF you want to
export (this should be a tagged release), then run:

```sh
export ocsf_p=/path/to/schema/working/copy
export ocsf_v=1.n.0

poetry run python -m ocsf.compile "$ocsf_p" --set-observable --prefix-extensions --set-object-types > schema_cache/schema-$ocsf_v.json
```