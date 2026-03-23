# CICIDS2017 dataset folders

Store local CICIDS2017 CSV files here when you want to use them for defensive
network-traffic analytics or dataset preparation inside AegisCore.

```text
data/cicids2017/
|-- raw/
|-- prepared/
```

Recommended `raw/` files based on the dataset you shared:
- `Monday-WorkingHours.pcap_ISCX.csv`
- `Tuesday-WorkingHours.pcap_ISCX.csv`
- `Wednesday-workingHours.pcap_ISCX.csv`
- `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv`
- `Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv`
- `Friday-WorkingHours-Morning.pcap_ISCX.csv`
- `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv`
- `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`

Use `prepared/` for:
- merged weekly exports
- cleaned column-normalized copies
- smaller slices for demo imports
- ML-ready subsets with selected features or labels

Only the folder scaffold is tracked in Git. Raw dataset files stay local.
