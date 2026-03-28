# Local dataset workspace

Use this folder for raw or prepared datasets that you want available inside the
project directory without committing the actual dataset files to Git.

Tracked here:

- folder structure
- `.gitkeep` placeholders
- short documentation
- `local_datasets.json` as a repo-safe manifest template

Ignored here:

- local Wazuh, Suricata, Nmap, and Hydra import files
- raw public datasets
- prepared CSV outputs
- any other large or licensed datasets

Recommended layout:

```text
data/
|-- imports/
|   |-- wazuh/
|   |-- suricata/
|   |-- nmap/
|   |-- hydra/
|-- unsw_nb15/
|   |-- raw/
|   |-- prepared/
|-- cicids2017/
|   |-- raw/
|   |-- prepared/
|-- local_datasets.json
```

Usage notes:

- Put your own local JSON import payloads for tool-specific testing in the
  matching `data/imports/<tool>/` folder.
- Put local `UNSW-NB15` source files in `data/unsw_nb15/raw/` and any cleaned
  or merged outputs in `data/unsw_nb15/prepared/`.
- Put local `CICIDS2017` source files in `data/cicids2017/raw/` and any cleaned
  or merged outputs in `data/cicids2017/prepared/`.
- Keep tiny shareable examples in `docs/` instead of `data/` if you want them
  versioned with the repo.
- Use `scripts/register_local_datasets.py` to update the local manifest safely.
