#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON in {path}: {exc}")
        sys.exit(2)

    if not isinstance(data, dict):
        print(f"[ERROR] Root must be an object: {path}")
        sys.exit(2)
    return data


def _flatten(data: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if not isinstance(key, str) or not key:
                continue
            next_prefix = f"{prefix}.{key}" if prefix else key
            out.update(_flatten(value, next_prefix))
        return out
    if isinstance(data, list):
        for idx, value in enumerate(data):
            next_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            out.update(_flatten(value, next_prefix))
        return out
    out[prefix] = data
    return out


def _validate_leaf_types(flat: Dict[str, Any]) -> bool:
    ok = True
    for key, value in flat.items():
        if isinstance(value, (dict, list)):
            print(f"[WARN] Non-leaf value at {key} (expected string)")
            ok = False
        elif not isinstance(value, str):
            print(f"[WARN] Non-string value at {key}: {type(value).__name__}")
            ok = False
    return ok


def _diff_keys(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, set]:
    keys_a = set(a.keys())
    keys_b = set(b.keys())
    return {
        "only_in_a": keys_a - keys_b,
        "only_in_b": keys_b - keys_a,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check i18n key parity between locales.")
    parser.add_argument("--zh", default="locales/zh-CN.json", help="Path to zh-CN locale JSON")
    parser.add_argument("--en", default="locales/en-US.json", help="Path to en-US locale JSON")
    args = parser.parse_args()

    zh_path = Path(args.zh)
    en_path = Path(args.en)

    zh = _flatten(_load_json(zh_path))
    en = _flatten(_load_json(en_path))

    ok = True
    if not _validate_leaf_types(zh) or not _validate_leaf_types(en):
        ok = False

    diff = _diff_keys(zh, en)
    if diff["only_in_a"]:
        ok = False
        print("[ERROR] Keys only in zh-CN:")
        for key in sorted(diff["only_in_a"]):
            print(f"  - {key}")

    if diff["only_in_b"]:
        ok = False
        print("[ERROR] Keys only in en-US:")
        for key in sorted(diff["only_in_b"]):
            print(f"  - {key}")

    if ok:
        print("[OK] i18n keys are aligned.")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
