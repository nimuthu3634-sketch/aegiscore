from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
LOCAL_MANIFEST_PATH = DATA_DIR / "local_datasets.json"
UNSW_PREPARED_OUTPUT = DATA_DIR / "unsw_nb15" / "prepared" / "unsw_nb15_prepared.csv"
UNSW_PREPARED_SUMMARY = DATA_DIR / "unsw_nb15" / "prepared" / "unsw_nb15_prepared.summary.json"
CICIDS_PREPARED_OUTPUT = DATA_DIR / "cicids2017" / "prepared" / "cicids2017_prepared.csv"
CICIDS_PREPARED_SUMMARY = DATA_DIR / "cicids2017" / "prepared" / "cicids2017_prepared.summary.json"


def _normalize_column_name(raw_name: object) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(raw_name).strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "column"


def _make_unique_columns(raw_columns: list[object]) -> list[str]:
    unique_columns: list[str] = []
    seen: dict[str, int] = {}
    for raw_name in raw_columns:
        base_name = _normalize_column_name(raw_name)
        suffix = seen.get(base_name, 0)
        unique_name = base_name if suffix == 0 else f"{base_name}_{suffix}"
        unique_columns.append(unique_name)
        seen[base_name] = suffix + 1
    return unique_columns


def _read_manifest_entries(manifest_path: Path, family: str) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Dataset manifest was not found: {manifest_path}. "
            "Create it with scripts/register_local_datasets.py or pass explicit file paths."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [entry for entry in manifest.get("datasets", []) if entry.get("family") == family]


def _find_role_path(entries: list[dict[str, Any]], role: str) -> Path | None:
    for entry in entries:
        if entry.get("role") == role and entry.get("path"):
            return Path(str(entry["path"]))
    return None


def _find_role_paths(entries: list[dict[str, Any]], prefix: str) -> list[Path]:
    matched_entries = [entry for entry in entries if str(entry.get("role") or "").startswith(prefix)]
    matched_entries.sort(key=lambda item: str(item.get("role") or ""))
    return [Path(str(entry["path"])) for entry in matched_entries if entry.get("path")]


def _ensure_paths_exist(paths: list[Path]) -> None:
    missing_paths = [str(path) for path in paths if not path.exists()]
    if missing_paths:
        missing_text = "\n".join(f"- {path}" for path in missing_paths)
        raise FileNotFoundError(f"Dataset file(s) not found:\n{missing_text}")


def _read_csv(path: Path, *, header: int | None = 0) -> pd.DataFrame:
    return pd.read_csv(path, header=header, low_memory=False, encoding="utf-8-sig")


def _standardize_frame_columns(frame: pd.DataFrame) -> pd.DataFrame:
    standardized = frame.copy()
    standardized.columns = _make_unique_columns(list(standardized.columns))
    return standardized


def _coerce_text_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column_name in normalized.select_dtypes(include=["object", "string"]).columns:
        normalized[column_name] = normalized[column_name].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return normalized


def _series_counts(series: pd.Series) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, value in series.fillna("__missing__").value_counts(dropna=False).items():
        counts[str(key)] = int(value)
    return counts


def _limit_rows_per_label(
    frame: pd.DataFrame,
    *,
    label_column: str | None,
    max_rows_per_label: int | None,
    random_seed: int,
) -> tuple[pd.DataFrame, bool]:
    if label_column is None or max_rows_per_label is None:
        return frame.reset_index(drop=True), False
    if max_rows_per_label < 1:
        raise ValueError("max_rows_per_label must be at least 1.")

    grouped_frames: list[pd.DataFrame] = []
    sampling_applied = False
    grouped = frame.assign(__label_group=frame[label_column].fillna("__missing__"))
    for _, group in grouped.groupby("__label_group", sort=True, dropna=False):
        current_group = group.drop(columns="__label_group")
        if len(current_group) > max_rows_per_label:
            sampling_applied = True
            grouped_frames.append(current_group.sample(n=max_rows_per_label, random_state=random_seed))
        else:
            grouped_frames.append(current_group)

    prepared = pd.concat(grouped_frames, ignore_index=False).sort_index().reset_index(drop=True)
    return prepared, sampling_applied


def _build_summary(
    *,
    dataset_family: str,
    frame: pd.DataFrame,
    source_files: list[Path],
    output_path: Path,
    summary_path: Path,
    label_column: str | None,
    sampling_column: str | None,
    max_rows_per_label: int | None,
    sampling_applied: bool,
) -> dict[str, Any]:
    numeric_columns = list(frame.select_dtypes(include=[np.number, "Int64", "Float64"]).columns)
    object_columns = [column for column in frame.columns if column not in numeric_columns]

    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_family": dataset_family,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": list(frame.columns),
        "numeric_column_count": int(len(numeric_columns)),
        "object_column_count": int(len(object_columns)),
        "numeric_columns": numeric_columns,
        "object_columns": object_columns,
        "source_files": [str(path) for path in source_files],
        "output_path": str(output_path),
        "summary_path": str(summary_path),
        "label_column": label_column,
        "sampling_column": sampling_column,
        "max_rows_per_label": max_rows_per_label,
        "sampling_applied": sampling_applied,
    }

    if label_column is not None and label_column in frame.columns:
        summary["label_distribution"] = _series_counts(frame[label_column])
    if "dataset_source_file" in frame.columns:
        summary["source_file_distribution"] = _series_counts(frame["dataset_source_file"])
    if "dataset_split" in frame.columns:
        summary["split_distribution"] = _series_counts(frame["dataset_split"])
    if "attack_cat" in frame.columns:
        summary["attack_category_distribution"] = _series_counts(frame["attack_cat"])

    return summary


def _write_output(frame: pd.DataFrame, output_path: Path, summary_path: Path, summary: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    summary_path.write_text(f"{json.dumps(summary, indent=2)}\n", encoding="utf-8")


def _resolve_unsw_paths(
    *,
    manifest_path: Path,
    training_path: Path | None,
    testing_path: Path | None,
    raw_parts: list[Path] | None,
    features_path: Path | None,
) -> tuple[Path | None, Path | None, list[Path], Path | None]:
    entries = _read_manifest_entries(manifest_path, "unsw_nb15")
    resolved_training = training_path or _find_role_path(entries, "training_split")
    resolved_testing = testing_path or _find_role_path(entries, "testing_split")
    resolved_raw_parts = raw_parts or _find_role_paths(entries, "raw_part_")
    resolved_features = features_path or _find_role_path(entries, "feature_reference")
    return resolved_training, resolved_testing, resolved_raw_parts, resolved_features


def _resolve_cicids_paths(*, manifest_path: Path, input_paths: list[Path] | None) -> list[Path]:
    if input_paths:
        return input_paths
    entries = _read_manifest_entries(manifest_path, "cicids2017")
    paths = [Path(str(entry["path"])) for entry in entries if entry.get("path")]
    paths.sort(key=lambda item: item.name.lower())
    return paths


def _load_unsw_feature_columns(features_path: Path) -> list[str]:
    features_frame = _read_csv(features_path)
    features_frame = _standardize_frame_columns(features_frame)
    name_column = "name" if "name" in features_frame.columns else features_frame.columns[1]
    raw_feature_names = [str(value).strip() for value in features_frame[name_column].tolist() if str(value).strip()]
    normalized_feature_names = _make_unique_columns(raw_feature_names)
    if "attack_cat" not in normalized_feature_names:
        normalized_feature_names.append("attack_cat")
    if "label" not in normalized_feature_names:
        normalized_feature_names.append("label")
    return normalized_feature_names


def _adapt_raw_columns(column_names: list[str], column_count: int) -> list[str]:
    adapted_columns = list(column_names)
    if len(adapted_columns) > column_count:
        return adapted_columns[:column_count]
    while len(adapted_columns) < column_count:
        adapted_columns.append(f"extra_col_{len(adapted_columns) + 1}")
    return adapted_columns


def _finalize_unsw_frame(
    frame: pd.DataFrame,
    *,
    max_rows_per_label: int | None,
    random_seed: int,
) -> tuple[pd.DataFrame, str | None, bool]:
    prepared = frame.copy()
    prepared = _coerce_text_columns(prepared)
    if "label" in prepared.columns:
        prepared["label"] = pd.to_numeric(prepared["label"], errors="coerce").astype("Int64")
    if "attack_cat" in prepared.columns:
        prepared["attack_cat"] = prepared["attack_cat"].fillna("").map(
            lambda value: value.strip() if isinstance(value, str) else str(value)
        )
        if "label" in prepared.columns:
            normal_mask = prepared["attack_cat"].eq("") & prepared["label"].fillna(0).eq(0)
            attack_mask = prepared["attack_cat"].eq("") & prepared["label"].fillna(0).eq(1)
            prepared.loc[normal_mask, "attack_cat"] = "Normal"
            prepared.loc[attack_mask, "attack_cat"] = "UnknownAttack"
    prepared["dataset_family"] = "unsw_nb15"

    sampling_column = "attack_cat" if "attack_cat" in prepared.columns else ("label" if "label" in prepared.columns else None)
    prepared, sampling_applied = _limit_rows_per_label(
        prepared,
        label_column=sampling_column,
        max_rows_per_label=max_rows_per_label,
        random_seed=random_seed,
    )
    return prepared, sampling_column, sampling_applied


def prepare_unsw_nb15_dataset(
    *,
    source_mode: str,
    manifest_path: Path,
    training_path: Path | None,
    testing_path: Path | None,
    raw_parts: list[Path] | None,
    features_path: Path | None,
    output_path: Path,
    summary_path: Path,
    max_rows_per_label: int | None,
    random_seed: int,
) -> dict[str, Any]:
    resolved_training, resolved_testing, resolved_raw_parts, resolved_features = _resolve_unsw_paths(
        manifest_path=manifest_path,
        training_path=training_path,
        testing_path=testing_path,
        raw_parts=raw_parts,
        features_path=features_path,
    )

    use_splits = source_mode == "splits" or (
        source_mode == "auto" and resolved_training is not None and resolved_testing is not None
    )
    use_raw = source_mode == "raw" or (source_mode == "auto" and not use_splits)

    source_files: list[Path] = []
    frames: list[pd.DataFrame] = []

    if use_splits:
        split_paths = [path for path in [resolved_training, resolved_testing] if path is not None]
        if not split_paths:
            raise ValueError("UNSW-NB15 split preparation requires training/testing CSV files.")
        _ensure_paths_exist(split_paths)
        for split_name, path in [("training", resolved_training), ("testing", resolved_testing)]:
            if path is None:
                continue
            frame = _standardize_frame_columns(_read_csv(path))
            frame["dataset_split"] = split_name
            frame["dataset_source_file"] = path.name
            frames.append(frame)
            source_files.append(path)

    if use_raw and not frames:
        if resolved_features is None:
            raise ValueError("UNSW-NB15 raw preparation requires the features reference CSV.")
        if not resolved_raw_parts:
            raise ValueError("UNSW-NB15 raw preparation requires at least one raw split CSV.")
        _ensure_paths_exist([resolved_features, *resolved_raw_parts])
        raw_columns = _load_unsw_feature_columns(resolved_features)
        source_files.append(resolved_features)
        for path in resolved_raw_parts:
            frame = _read_csv(path, header=None)
            frame.columns = _make_unique_columns(_adapt_raw_columns(raw_columns, frame.shape[1]))
            frame["dataset_split"] = path.stem
            frame["dataset_source_file"] = path.name
            frames.append(frame)
            source_files.append(path)

    if not frames:
        raise ValueError("No UNSW-NB15 source files could be resolved for preparation.")

    combined = pd.concat(frames, ignore_index=True)
    combined, sampling_column, sampling_applied = _finalize_unsw_frame(
        combined,
        max_rows_per_label=max_rows_per_label,
        random_seed=random_seed,
    )
    summary = _build_summary(
        dataset_family="unsw_nb15",
        frame=combined,
        source_files=source_files,
        output_path=output_path,
        summary_path=summary_path,
        label_column="attack_cat" if "attack_cat" in combined.columns else ("label" if "label" in combined.columns else None),
        sampling_column=sampling_column,
        max_rows_per_label=max_rows_per_label,
        sampling_applied=sampling_applied,
    )
    summary["source_mode"] = "splits" if use_splits else "raw"
    _write_output(combined, output_path, summary_path, summary)
    return summary


def _finalize_cicids_frame(
    frame: pd.DataFrame,
    *,
    max_rows_per_label: int | None,
    random_seed: int,
) -> tuple[pd.DataFrame, str | None, bool]:
    prepared = frame.copy()
    prepared = _coerce_text_columns(prepared)
    prepared = prepared.replace([np.inf, -np.inf], np.nan)
    if "label" not in prepared.columns:
        raise ValueError("CICIDS2017 preparation requires a Label column.")
    prepared["label"] = prepared["label"].fillna("UNKNOWN").map(
        lambda value: value.strip() if isinstance(value, str) else str(value)
    )
    prepared["label_binary"] = prepared["label"].map(lambda value: 0 if value.upper() == "BENIGN" else 1).astype(int)
    prepared["dataset_family"] = "cicids2017"
    sampling_column = "label"
    prepared, sampling_applied = _limit_rows_per_label(
        prepared,
        label_column=sampling_column,
        max_rows_per_label=max_rows_per_label,
        random_seed=random_seed,
    )
    return prepared, sampling_column, sampling_applied


def prepare_cicids2017_dataset(
    *,
    manifest_path: Path,
    input_paths: list[Path] | None,
    output_path: Path,
    summary_path: Path,
    max_rows_per_label: int | None,
    random_seed: int,
) -> dict[str, Any]:
    resolved_inputs = _resolve_cicids_paths(manifest_path=manifest_path, input_paths=input_paths)
    if not resolved_inputs:
        raise ValueError("No CICIDS2017 CSV files were provided or found in the local dataset manifest.")
    _ensure_paths_exist(resolved_inputs)

    frames: list[pd.DataFrame] = []
    for path in resolved_inputs:
        frame = _standardize_frame_columns(_read_csv(path))
        frame["dataset_source_file"] = path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined, sampling_column, sampling_applied = _finalize_cicids_frame(
        combined,
        max_rows_per_label=max_rows_per_label,
        random_seed=random_seed,
    )
    summary = _build_summary(
        dataset_family="cicids2017",
        frame=combined,
        source_files=resolved_inputs,
        output_path=output_path,
        summary_path=summary_path,
        label_column="label",
        sampling_column=sampling_column,
        max_rows_per_label=max_rows_per_label,
        sampling_applied=sampling_applied,
    )
    _write_output(combined, output_path, summary_path, summary)
    return summary


def _add_common_output_args(parser: argparse.ArgumentParser, *, output_path: Path, summary_path: Path) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=output_path,
        help=f"Prepared CSV output path. Default: {output_path}",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=summary_path,
        help=f"Summary JSON output path. Default: {summary_path}",
    )
    parser.add_argument(
        "--max-rows-per-label",
        type=int,
        help="Optional balanced cap per label/category to keep the prepared dataset demo-friendly.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed used for any per-label sampling. Default: 42",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare local public security datasets such as UNSW-NB15 and CICIDS2017 "
            "for defensive analytics and ML workflows in AegisCore."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    unsw_parser = subparsers.add_parser(
        "unsw_nb15",
        help="Merge and normalize UNSW-NB15 source files into a prepared CSV.",
    )
    unsw_parser.add_argument(
        "--manifest",
        type=Path,
        default=LOCAL_MANIFEST_PATH,
        help=f"Local dataset manifest path. Default: {LOCAL_MANIFEST_PATH}",
    )
    unsw_parser.add_argument(
        "--source",
        choices=["auto", "splits", "raw"],
        default="auto",
        help=(
            "Use training/testing splits, headerless raw parts, or auto-detect from the manifest. "
            "Default: auto"
        ),
    )
    unsw_parser.add_argument("--training", type=Path, help="Optional path to UNSW-NB15 training CSV.")
    unsw_parser.add_argument("--testing", type=Path, help="Optional path to UNSW-NB15 testing CSV.")
    unsw_parser.add_argument(
        "--raw-part",
        type=Path,
        action="append",
        help="Optional path to a headerless UNSW-NB15 raw split CSV. Repeat for multiple files.",
    )
    unsw_parser.add_argument(
        "--features",
        type=Path,
        help="Optional path to the UNSW-NB15 feature reference CSV used for headerless raw splits.",
    )
    _add_common_output_args(
        unsw_parser,
        output_path=UNSW_PREPARED_OUTPUT,
        summary_path=UNSW_PREPARED_SUMMARY,
    )

    cicids_parser = subparsers.add_parser(
        "cicids2017",
        help="Merge and normalize CICIDS2017 CSV files into a prepared CSV.",
    )
    cicids_parser.add_argument(
        "--manifest",
        type=Path,
        default=LOCAL_MANIFEST_PATH,
        help=f"Local dataset manifest path. Default: {LOCAL_MANIFEST_PATH}",
    )
    cicids_parser.add_argument(
        "--input",
        type=Path,
        action="append",
        help="Optional path to a CICIDS2017 CSV. Repeat for multiple files.",
    )
    _add_common_output_args(
        cicids_parser,
        output_path=CICIDS_PREPARED_OUTPUT,
        summary_path=CICIDS_PREPARED_SUMMARY,
    )

    all_parser = subparsers.add_parser(
        "all",
        help="Prepare both UNSW-NB15 and CICIDS2017 using the local dataset manifest.",
    )
    all_parser.add_argument(
        "--manifest",
        type=Path,
        default=LOCAL_MANIFEST_PATH,
        help=f"Local dataset manifest path. Default: {LOCAL_MANIFEST_PATH}",
    )
    all_parser.add_argument(
        "--max-rows-per-label",
        type=int,
        help="Optional balanced cap applied to both prepared datasets.",
    )
    all_parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed used for any per-label sampling. Default: 42",
    )

    return parser


def _run_unsw_command(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_unsw_nb15_dataset(
        source_mode=args.source,
        manifest_path=args.manifest,
        training_path=args.training,
        testing_path=args.testing,
        raw_parts=args.raw_part,
        features_path=args.features,
        output_path=args.output,
        summary_path=args.summary_json,
        max_rows_per_label=args.max_rows_per_label,
        random_seed=args.random_seed,
    )


def _run_cicids_command(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_cicids2017_dataset(
        manifest_path=args.manifest,
        input_paths=args.input,
        output_path=args.output,
        summary_path=args.summary_json,
        max_rows_per_label=args.max_rows_per_label,
        random_seed=args.random_seed,
    )


def _run_all_command(args: argparse.Namespace) -> int:
    unsw_summary = prepare_unsw_nb15_dataset(
        source_mode="auto",
        manifest_path=args.manifest,
        training_path=None,
        testing_path=None,
        raw_parts=None,
        features_path=None,
        output_path=UNSW_PREPARED_OUTPUT,
        summary_path=UNSW_PREPARED_SUMMARY,
        max_rows_per_label=args.max_rows_per_label,
        random_seed=args.random_seed,
    )
    cicids_summary = prepare_cicids2017_dataset(
        manifest_path=args.manifest,
        input_paths=None,
        output_path=CICIDS_PREPARED_OUTPUT,
        summary_path=CICIDS_PREPARED_SUMMARY,
        max_rows_per_label=args.max_rows_per_label,
        random_seed=args.random_seed,
    )
    print(f"Prepared UNSW-NB15 -> {unsw_summary['output_path']}")
    print(f"Prepared CICIDS2017 -> {cicids_summary['output_path']}")
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "unsw_nb15":
            summary = _run_unsw_command(args)
            print(f"Prepared UNSW-NB15 -> {summary['output_path']}")
            print(f"Rows written: {summary['row_count']}")
            return 0
        if args.command == "cicids2017":
            summary = _run_cicids_command(args)
            print(f"Prepared CICIDS2017 -> {summary['output_path']}")
            print(f"Rows written: {summary['row_count']}")
            return 0
        return _run_all_command(args)
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
