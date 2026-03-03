import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_SPLITS = ["train", "valid", "test"]
DEFAULT_CANONICAL = "colony"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit COCO labels and optionally remap categories to canonical names"
    )
    parser.add_argument("--dataset-root", required=True, help="COCO dataset root")
    parser.add_argument(
        "--splits",
        nargs="+",
        default=DEFAULT_SPLITS,
        help="Dataset splits to process (default: train valid test)",
    )
    parser.add_argument(
        "--ann-name",
        default="_annotations.coco.json",
        help="Annotation file name in each split directory",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help="Output dataset root (default: <dataset-root>.remapped)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Rewrite annotation file in the source split directory",
    )
    parser.add_argument(
        "--drop-empty-images",
        action="store_true",
        help="Drop images that end up with zero annotations after filtering",
    )
    parser.add_argument(
        "--category-map-file",
        default="",
        help="Optional JSON file mapping old category names to new names",
    )
    parser.add_argument(
        "--canonical-name",
        default=DEFAULT_CANONICAL,
        help="Fallback category name for noisy labels like '0' or 'object'",
    )
    parser.add_argument(
        "--copy-images",
        action="store_true",
        help="Copy images to output split directory when not in-place",
    )
    parser.add_argument(
        "--report-json",
        default="",
        help="Path for audit/remap summary report (default under output root)",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_label(name: str) -> str:
    return name.strip().lower().replace("-", " ").replace("_", " ")


def guess_canonical_name(name: str, fallback: str) -> str:
    token = normalize_label(name)
    if token in {
        "0",
        "object",
        "objects",
        "colony",
        "colonies",
        "bacteria",
        "bacterium",
    }:
        return fallback
    return token if token else fallback


def maybe_load_name_map(path: str) -> dict[str, str]:
    if not path:
        return {}
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("category-map-file must be a JSON object")
    out: dict[str, str] = {}
    for k, v in content.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError("category-map-file keys and values must be strings")
        out[normalize_label(k)] = normalize_label(v)
    return out


def remap_split(
    split_dir: Path,
    ann_name: str,
    out_split_dir: Path,
    in_place: bool,
    copy_images: bool,
    drop_empty_images: bool,
    fallback_name: str,
    explicit_map: dict[str, str],
) -> dict[str, Any]:
    ann_path = split_dir / ann_name
    if not ann_path.exists():
        return {
            "split": split_dir.name,
            "status": "missing_annotation",
            "annotation": str(ann_path),
        }

    coco = load_json(ann_path)
    images = coco.get("images", [])
    annotations = coco.get("annotations", [])
    categories = coco.get("categories", [])

    cat_by_id: dict[int, str] = {}
    for c in categories:
        cid = int(c.get("id", -1))
        cname = str(c.get("name", "")).strip()
        cat_by_id[cid] = cname

    old_counts = Counter()
    invalid_bbox = 0
    category_name_map: dict[int, str] = {}

    for cid, cname in cat_by_id.items():
        norm = normalize_label(cname)
        mapped = explicit_map.get(norm, guess_canonical_name(cname, fallback_name))
        category_name_map[cid] = mapped

    new_category_ids: dict[str, int] = {}
    new_categories: list[dict[str, Any]] = []

    def ensure_new_cat(name: str) -> int:
        if name in new_category_ids:
            return new_category_ids[name]
        new_id = len(new_category_ids) + 1
        new_category_ids[name] = new_id
        new_categories.append({"id": new_id, "name": name, "supercategory": "bacteria"})
        return new_id

    remapped_annotations: list[dict[str, Any]] = []
    used_image_ids = set()

    for idx, ann in enumerate(annotations, start=1):
        old_cat = int(ann.get("category_id", -1))
        old_counts[old_cat] += 1
        bbox = ann.get("bbox", [0, 0, 0, 0])
        if not isinstance(bbox, list) or len(bbox) != 4:
            invalid_bbox += 1
            continue

        w = float(bbox[2])
        h = float(bbox[3])
        if w <= 0 or h <= 0:
            invalid_bbox += 1
            continue

        mapped_name = category_name_map.get(old_cat, fallback_name)
        new_cat = ensure_new_cat(mapped_name)

        new_ann = dict(ann)
        new_ann["id"] = idx
        new_ann["category_id"] = new_cat
        new_ann["area"] = float(w * h)
        remapped_annotations.append(new_ann)
        used_image_ids.add(int(new_ann.get("image_id", -1)))

    if drop_empty_images:
        remapped_images = [
            img for img in images if int(img.get("id", -1)) in used_image_ids
        ]
    else:
        remapped_images = images

    remapped = {
        "info": coco.get("info", {}),
        "licenses": coco.get("licenses", []),
        "images": remapped_images,
        "annotations": remapped_annotations,
        "categories": new_categories,
    }

    if in_place:
        out_ann_path = ann_path
    else:
        out_ann_path = out_split_dir / ann_name
    save_json(out_ann_path, remapped)

    copied_images = 0
    if (not in_place) and copy_images:
        out_split_dir.mkdir(parents=True, exist_ok=True)
        for img in remapped_images:
            fname = str(img.get("file_name", ""))
            if not fname:
                continue
            src = split_dir / fname
            dst = out_split_dir / fname
            if not src.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            copied_images += 1

    old_name_counts = {
        (cat_by_id.get(cid, "<missing>") or "<missing>"): int(count)
        for cid, count in sorted(old_counts.items(), key=lambda kv: kv[0])
    }
    new_name_counts = Counter()
    for ann in remapped_annotations:
        cid = int(ann["category_id"])
        cname = next(
            (c["name"] for c in new_categories if int(c["id"]) == cid), "<missing>"
        )
        new_name_counts[cname] += 1

    return {
        "split": split_dir.name,
        "status": "ok",
        "source_annotation": str(ann_path),
        "output_annotation": str(out_ann_path),
        "images_before": len(images),
        "images_after": len(remapped_images),
        "annotations_before": len(annotations),
        "annotations_after": len(remapped_annotations),
        "invalid_bbox_filtered": invalid_bbox,
        "categories_before": [
            {"id": int(c.get("id", -1)), "name": str(c.get("name", ""))}
            for c in categories
        ],
        "categories_after": new_categories,
        "old_category_counts": old_name_counts,
        "new_category_counts": dict(new_name_counts),
        "copied_images": copied_images,
    }


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root)
    if not dataset_root.exists():
        raise FileNotFoundError(f"dataset root not found: {dataset_root}")

    explicit_map = maybe_load_name_map(args.category_map_file)

    output_root = (
        Path(args.output_root)
        if args.output_root
        else Path(str(dataset_root) + ".remapped")
    )
    if args.in_place:
        output_root = dataset_root

    report: dict[str, Any] = {
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "in_place": bool(args.in_place),
        "splits": args.splits,
        "annotation_name": args.ann_name,
        "explicit_map": explicit_map,
        "results": [],
    }

    for split in args.splits:
        split_dir = dataset_root / split
        out_split_dir = output_root / split
        result = remap_split(
            split_dir=split_dir,
            ann_name=args.ann_name,
            out_split_dir=out_split_dir,
            in_place=args.in_place,
            copy_images=args.copy_images,
            drop_empty_images=args.drop_empty_images,
            fallback_name=normalize_label(args.canonical_name),
            explicit_map=explicit_map,
        )
        report["results"].append(result)
        print(
            f"[{split}] {result.get('status')} -> {result.get('output_annotation', result.get('annotation', 'n/a'))}"
        )

    if args.report_json:
        report_path = Path(args.report_json)
    else:
        report_path = output_root / "remap_audit_report.json"
    save_json(report_path, report)
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
