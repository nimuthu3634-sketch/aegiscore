# UNSW-NB15 dataset folders

Store local UNSW-NB15 CSV files here when you want to use them for defensive
analytics, feature experiments, or model training inside AegisCore.

```text
data/unsw_nb15/
|-- raw/
|-- prepared/
```

Recommended `raw/` files based on the dataset you shared:
- `NUSW-NB15_features.csv`
- `UNSW_NB15_training-set.csv`
- `UNSW_NB15_testing-set.csv`
- `UNSW-NB15_1.csv`
- `UNSW-NB15_2.csv`
- `UNSW-NB15_3.csv`
- `UNSW-NB15_4.csv`
- `UNSW-NB15_LIST_EVENTS.csv`

Use `prepared/` for:
- merged CSV files
- cleaned column-normalized copies
- smaller demo-friendly slices
- train and evaluation subsets produced for the ML workflow

Only the folder scaffold is tracked in Git. Raw dataset files stay local.
