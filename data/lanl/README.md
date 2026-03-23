# LANL dataset folders

Store official LANL Comprehensive dataset files locally in this structure:

```text
data/lanl/
|-- raw/
|-- prepared/
```

Suggested `raw/` filenames:
- `auth.txt.gz`
- `dns.txt.gz`
- `flows.txt.gz`
- `redteam.txt.gz`

Suggested `prepared/` outputs:
- `auth-alert-candidates-1000.txt.gz`
- `auth-alert-candidates-1000.summary.json`
- `dns-first-1000.txt.gz`
- `flows-alert-candidates-1000.txt.gz`

Helper commands:

```powershell
py scripts/lanl_prepare.py download --dataset-type auth --url "<direct official LANL file URL>"
py scripts/lanl_prepare.py prepare --dataset-type auth --input data/lanl/raw/auth.txt.gz --output data/lanl/prepared/auth-alert-candidates-1000.txt.gz --redteam-input data/lanl/raw/redteam.txt.gz --only-alert-candidates --max-records 1000
```

Only the folder scaffold is tracked in Git. Actual dataset files in `raw/` and
`prepared/` stay local.
