from collections.abc import Iterable


def next_prefixed_id(prefix: str, existing_ids: Iterable[str]) -> str:
    next_number = 1
    prefix_with_separator = f"{prefix}-"

    for record_id in existing_ids:
        if not isinstance(record_id, str) or not record_id.startswith(prefix_with_separator):
            continue

        suffix = record_id[len(prefix_with_separator) :]
        if not suffix.isdigit():
            continue

        next_number = max(next_number, int(suffix) + 1)

    return f"{prefix}-{next_number:03d}"
