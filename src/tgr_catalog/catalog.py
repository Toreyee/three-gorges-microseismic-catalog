"""Read, label, validate, and integrate hypoDD catalog products.

The project contains two distinct hypoDD products:

* ``hypoDD.loc``: 18-column initial locations supplied to hypoDD.
* ``hypoDD.reloc``: 24-column double-difference relocation output.

They are deliberately kept separate because treating ``.loc`` as relocated output
changes both the scientific interpretation and the number of retained events.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


LOC_COLUMNS = [
    "event_id",
    "latitude_deg",
    "longitude_deg",
    "depth_km",
    "x_m",
    "y_m",
    "z_m",
    "err_x_m",
    "err_y_m",
    "err_z_m",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "magnitude",
    "cluster_id",
]

RELOC_COLUMNS = [
    *LOC_COLUMNS[:-1],
    "ncc_p",
    "ncc_s",
    "nct_p",
    "nct_s",
    "rms_cc_s",
    "rms_ct_s",
    "cluster_id",
]

MODEL_CODES = {
    "EQT": "E",
    "RNN": "R",
    "Unet": "U",
    "LPPNL": "L",
    "lppnl": "L",
}
CODE_MODELS = {
    "E": "EQTransformer",
    "R": "RNN",
    "U": "Unet",
    "L": "LPPNL",
}
SINGLE_MODEL_CATEGORIES = {
    "EE": ("EQTransformer",),
    "RR": ("RNN",),
    "UU": ("Unet",),
    "LL": ("LPPNL",),
}


@dataclass(frozen=True)
class CatalogEvent:
    """One source event retained together with its original text line."""

    timestamp: pd.Timestamp
    model: str
    quality: float
    raw_line: str


def read_hypodd_catalog(path: str | Path, kind: str = "auto") -> pd.DataFrame:
    """Read an 18-column ``.loc`` or 24-column ``.reloc`` catalog.

    Parameters
    ----------
    path:
        Whitespace-delimited hypoDD output.
    kind:
        ``"loc"``, ``"reloc"``, or ``"auto"``. Auto-detection is based on
        the observed number of columns and fails closed for unexpected schemas.
    """

    catalog_path = Path(path)
    if not catalog_path.is_file():
        raise FileNotFoundError(catalog_path)

    frame = pd.read_csv(
        catalog_path,
        sep=r"\s+",
        header=None,
        comment="#",
        engine="python",
    )
    observed = frame.shape[1]
    if kind == "auto":
        kind = {len(LOC_COLUMNS): "loc", len(RELOC_COLUMNS): "reloc"}.get(observed, "")
    if kind not in {"loc", "reloc"}:
        raise ValueError(
            f"Cannot determine catalog kind for {catalog_path}: {observed} columns"
        )

    columns = LOC_COLUMNS if kind == "loc" else RELOC_COLUMNS
    if observed != len(columns):
        raise ValueError(
            f"Expected {len(columns)} columns for {kind}, found {observed}: {catalog_path}"
        )

    frame.columns = columns
    frame.attrs["catalog_kind"] = kind
    frame.attrs["source_path"] = str(catalog_path)
    return add_event_timestamps(frame)


def add_event_timestamps(frame: pd.DataFrame) -> pd.DataFrame:
    """Add a timezone-naive UTC timestamp while correctly handling second overflow."""

    required = {"year", "month", "day", "hour", "minute", "second"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing time columns: {sorted(missing)}")

    result = frame.copy()
    base = pd.to_datetime(
        {
            "year": result["year"].astype(int),
            "month": result["month"].astype(int),
            "day": result["day"].astype(int),
            "hour": result["hour"].astype(int),
            "minute": result["minute"].astype(int),
        },
        errors="raise",
    )
    result.insert(
        0,
        "timestamp_utc",
        base + pd.to_timedelta(result["second"].astype(float), unit="s"),
    )
    result.attrs.update(frame.attrs)
    return result


def category_models(category: str) -> tuple[str, ...]:
    """Expand a historical category code such as ``ERUL`` or ``EE``."""

    normalized = category.upper().replace("_OUTPUT", "")
    if normalized in SINGLE_MODEL_CATEGORIES:
        return SINGLE_MODEL_CATEGORIES[normalized]
    unknown = set(normalized).difference(CODE_MODELS)
    if unknown:
        raise ValueError(f"Unknown model category {category!r}: {sorted(unknown)}")
    return tuple(CODE_MODELS[code] for code in "ERUL" if code in normalized)


def _category_from_models(models: Iterable[str]) -> str:
    codes = {MODEL_CODES[model] for model in models}
    if len(codes) == 1:
        code = next(iter(codes))
        return code * 2
    return "".join(code for code in "ERUL" if code in codes)


def combine_category_directory(
    directory: str | Path,
    kind: str,
    pattern: str = "*.txt",
) -> pd.DataFrame:
    """Combine the 15 historical model-category files and retain provenance labels."""

    root = Path(directory)
    frames: list[pd.DataFrame] = []
    for path in sorted(root.glob(pattern)):
        stem = path.stem.replace("_output", "")
        try:
            models = category_models(stem)
        except ValueError:
            continue
        frame = read_hypodd_catalog(path, kind=kind)
        frame.insert(1, "model_combination", "+".join(models))
        frame.insert(2, "category_code", stem.upper())
        frame.insert(3, "source_file", path.name)
        frames.append(frame)

    if len(frames) != 15:
        raise ValueError(f"Expected 15 model-category files in {root}, found {len(frames)}")
    result = pd.concat(frames, ignore_index=True)
    return result.sort_values("timestamp_utc", kind="stable").reset_index(drop=True)


def _cluster_sorted_events(
    events: Sequence[CatalogEvent], threshold_seconds: float
) -> list[list[CatalogEvent]]:
    """Single-link time clustering utility for optional catalog experiments."""

    clusters: list[list[CatalogEvent]] = []
    current: list[CatalogEvent] = []
    for event in sorted(events, key=lambda item: item.timestamp):
        if not current:
            current = [event]
            continue
        delta = (event.timestamp - current[-1].timestamp).total_seconds()
        if abs(delta) <= threshold_seconds:
            current.append(event)
        else:
            clusters.append(current)
            current = [event]
    if current:
        clusters.append(current)
    return clusters


def integrate_model_catalogs(
    model_paths: Mapping[str, str | Path],
    *,
    kind: str = "reloc",
    threshold_seconds: float = 2.0,
    quality_column: str = "rms_ct_s",
    select: str = "min",
) -> dict[str, list[str]]:
    """Integrate model catalogs and return original lines grouped by model category.

    This is a generic utility for optional cross-model experiments with catalogs
    that provide a finite quality field. It is not the builder for the archived
    6,344-event manuscript catalog; that product is verified from its preserved
    category partitions by ``scripts/10_verify_manuscript_catalog.py``.
    """

    if select not in {"min", "max"}:
        raise ValueError("select must be 'min' or 'max'")

    events: list[CatalogEvent] = []
    for model, path in model_paths.items():
        if model not in MODEL_CODES:
            raise ValueError(f"Unsupported model name: {model}")
        frame = read_hypodd_catalog(path, kind=kind)
        if quality_column not in frame.columns:
            raise ValueError(f"{quality_column!r} is unavailable in {kind} catalog {path}")

        raw_lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(raw_lines) != len(frame):
            raise ValueError(f"Line count changed while reading {path}")
        for timestamp, quality, raw_line in zip(
            frame["timestamp_utc"], frame[quality_column], raw_lines, strict=True
        ):
            events.append(
                CatalogEvent(
                    timestamp=pd.Timestamp(timestamp),
                    model=model,
                    quality=float(quality),
                    raw_line=raw_line,
                )
            )

    grouped: dict[str, list[str]] = {
        code: []
        for code in ("ERUL", "ERU", "ERL", "EUL", "RUL", "ER", "EU", "EL", "RU", "RL", "UL", "EE", "RR", "UU", "LL")
    }
    chooser = min if select == "min" else max
    for cluster in _cluster_sorted_events(events, threshold_seconds):
        category = _category_from_models(event.model for event in cluster)
        finite = [event for event in cluster if np.isfinite(event.quality)]
        candidates = finite or cluster
        selected = chooser(candidates, key=lambda item: item.quality)
        grouped[category].append(selected.raw_line)
    return grouped


def write_integration_result(groups: Mapping[str, Sequence[str]], output_dir: str | Path) -> None:
    """Write category files plus one chronologically sorted combined file."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    combined: list[tuple[pd.Timestamp, str]] = []
    for category, lines in groups.items():
        path = root / f"{category}.txt"
        path.write_text("".join(f"{line.rstrip()}\n" for line in lines), encoding="utf-8")
        if lines:
            temp = root / f".{category}.parse.tmp"
            temp.write_text("".join(f"{line.rstrip()}\n" for line in lines), encoding="utf-8")
            frame = read_hypodd_catalog(temp, kind="auto")
            temp.unlink()
            combined.extend(zip(frame["timestamp_utc"], lines, strict=True))
    combined.sort(key=lambda pair: pair[0])
    (root / "ALL.txt").write_text(
        "".join(f"{line.rstrip()}\n" for _, line in combined), encoding="utf-8"
    )

