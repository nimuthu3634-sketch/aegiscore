# Tool-specific local imports

Use these folders when you want to keep your own local import payloads next to
the project without committing them to Git.

Suggested examples:
- `data/imports/wazuh/alerts-lab-01.json`
- `data/imports/suricata/events-lab-01.json`
- `data/imports/nmap/results-lab-01.json`
- `data/imports/hydra/results-lab-01.json`

These files are ignored by Git on purpose. If you want a tiny tracked example,
place it in `docs/` instead.
