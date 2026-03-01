import csv
import json
import shutil
import time
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import cv2
import numpy as np


@dataclass
class StoredRecord:
    timestamp: float
    strain_name: str
    batch_id: str
    source_type: str
    source_path: str
    annotated_path: str
    model_path: str
    score_threshold: float
    nms_iou: float
    high_conf_threshold: float
    count: int
    high_count: int
    low_count: int
    latency_ms: float
    top_score: float
    avg_score: float
    details: list[dict]
    summary_text: str


class StorageService:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or (Path.home() / ".cnn_microai_pi"))
        self.batches_root = self.base_dir / "batches"
        self.batches_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_component(v: str) -> str:
        v = v.strip()
        if not v:
            return "unknown"
        chars = []
        for ch in v:
            if ch.isalnum() or ch in ("-", "_"):
                chars.append(ch)
            else:
                chars.append("_")
        cleaned = "".join(chars).strip("_")
        return cleaned or "unknown"

    def _batch_root(self, strain_name: str, batch_id: str) -> Path:
        s = self._sanitize_component(strain_name)
        b = self._sanitize_component(batch_id)
        return self.batches_root / s / b

    def _batch_dirs(self, strain_name: str, batch_id: str) -> dict:
        root = self._batch_root(strain_name, batch_id)
        dirs = {
            "root": root,
            "captures": root / "captures",
            "imports": root / "imports",
            "results": root / "results",
            "exports": root / "exports",
            "history": root / "history",
        }
        for p in dirs.values():
            p.mkdir(parents=True, exist_ok=True)
        return dirs

    @staticmethod
    def _timestamp_label(fmt: str) -> str:
        try:
            return datetime.now().strftime(fmt)
        except Exception:
            return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _build_name(
        self, prefix: str, strain_name: str, batch_id: str, ts_fmt: str, suffix: str
    ) -> str:
        s = self._sanitize_component(strain_name)
        b = self._sanitize_component(batch_id)
        t = self._timestamp_label(ts_fmt)
        ms = int(time.time() * 1000) % 1000
        return f"{prefix}_{s}_{b}_{t}_{ms:03d}{suffix}"

    def save_capture(
        self, image_bgr: np.ndarray, strain_name: str, batch_id: str, ts_fmt: str
    ) -> Path:
        d = self._batch_dirs(strain_name, batch_id)["captures"]
        p = d / self._build_name("RAW", strain_name, batch_id, ts_fmt, ".jpg")
        cv2.imwrite(str(p), image_bgr)
        return p

    def save_imported_file(
        self, src_path: str, strain_name: str, batch_id: str, ts_fmt: str
    ) -> Path:
        d = self._batch_dirs(strain_name, batch_id)["imports"]
        src = Path(src_path)
        suffix = src.suffix.lower() if src.suffix else ".jpg"
        p = d / self._build_name("IMP", strain_name, batch_id, ts_fmt, suffix)
        shutil.copy2(src, p)
        return p

    def import_from_usb_dir(
        self, usb_dir: str, strain_name: str, batch_id: str, ts_fmt: str
    ) -> List[Path]:
        root = Path(usb_dir)
        if not root.exists() or not root.is_dir():
            return []
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        copied: List[Path] = []
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                copied.append(
                    self.save_imported_file(str(p), strain_name, batch_id, ts_fmt)
                )
        return copied

    def save_annotated(
        self, image_bgr: np.ndarray, strain_name: str, batch_id: str, ts_fmt: str
    ) -> Path:
        d = self._batch_dirs(strain_name, batch_id)["results"]
        p = d / self._build_name("ANN", strain_name, batch_id, ts_fmt, ".jpg")
        cv2.imwrite(str(p), image_bgr)
        return p

    def _history_file(self, strain_name: str, batch_id: str) -> Path:
        d = self._batch_dirs(strain_name, batch_id)["history"]
        return d / "history.jsonl"

    def append_history(self, rec: StoredRecord) -> None:
        fp = self._history_file(rec.strain_name, rec.batch_id)
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")

    def load_history(
        self, strain_name: str, batch_id: str, limit: int = 200
    ) -> List[dict]:
        fp = self._history_file(strain_name, batch_id)
        if not fp.exists():
            return []
        rows: List[dict] = []
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        rows.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return rows[:limit]

    def export_batch_report(
        self, strain_name: str, batch_id: str, ts_fmt: str
    ) -> tuple[Path, Path]:
        dirs = self._batch_dirs(strain_name, batch_id)
        rows = self.load_history(strain_name, batch_id, limit=1_000_000)
        export_csv = dirs["exports"] / self._build_name(
            "REPORT", strain_name, batch_id, ts_fmt, ".csv"
        )
        fields = [
            "timestamp",
            "strain_name",
            "batch_id",
            "source_type",
            "source_path",
            "annotated_path",
            "model_path",
            "score_threshold",
            "nms_iou",
            "high_conf_threshold",
            "count",
            "high_count",
            "low_count",
            "latency_ms",
            "top_score",
            "avg_score",
            "summary_text",
        ]
        with open(export_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in fields})

        zip_path = dirs["exports"] / self._build_name(
            "EXPORT", strain_name, batch_id, ts_fmt, ".zip"
        )
        with zipfile.ZipFile(
            zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
            zf.write(export_csv, arcname=f"exports/{export_csv.name}")
            history_file = self._history_file(strain_name, batch_id)
            if history_file.exists():
                zf.write(history_file, arcname="history/history.jsonl")
            for folder in (dirs["captures"], dirs["imports"], dirs["results"]):
                if not folder.exists():
                    continue
                for p in folder.rglob("*"):
                    if p.is_file():
                        rel = p.relative_to(dirs["root"]).as_posix()
                        zf.write(p, arcname=rel)
        return export_csv, zip_path

    @staticmethod
    def default_usb_roots() -> Iterable[str]:
        user = Path.home().name
        return [
            f"/media/{user}",
            f"/run/media/{user}",
            "/media/pi",
        ]
