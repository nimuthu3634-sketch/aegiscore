# Local dataset workspace

Use this folder for raw or prepared datasets that you want available inside the
project directory without committing the actual dataset files to Git.

Tracked here:
- folder structure
- `.gitkeep` placeholders
- short documentation

Ignored here:
- raw LANL downloads
- prepared LANL slices
- local Wazuh, Suricata, Nmap, and Hydra import files
- any other large or licensed datasets

Recommended layout:

```text
data/
|-- lanl/
|   |-- raw/
|   |-- prepared/
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
```

Usage notes:
- Put official LANL files such as `auth.txt.gz`, `dns.txt.gz`, `flows.txt.gz`,
  and `redteam.txt.gz` in `data/lanl/raw/`.
- Put smaller prepared LANL slices and optional summary JSON files in
  `data/lanl/prepared/`.
- Put your own local JSON import payloads for tool-specific testing in the
  matching `data/imports/<tool>/` folder.
- Put local `UNSW-NB15` source files in `data/unsw_nb15/raw/` and any cleaned
  or merged outputs in `data/unsw_nb15/prepared/`.
- Put local `CICIDS2017` source files in `data/cicids2017/raw/` and any cleaned
  or merged outputs in `data/cicids2017/prepared/`.
- Keep tiny shareable examples in `docs/` instead of `data/` if you want them
  versioned with the repo.
