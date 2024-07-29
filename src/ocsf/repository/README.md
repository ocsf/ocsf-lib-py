# OCSF Repository

The `ocsf.repository` package represents an OCSF repository (a set of schema definitions using the OCSF).

## Examples

```python
from ocsf.repository import read_repo

repo = read_repo("path/to/ocsf-schema")

for path in repo.paths():
    print(path)
```
