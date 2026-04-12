import json
import os
import random
import uuid
from pathlib import Path

def _load_config() -> dict:
    cfg_path = Path(__file__).parent / "trainer_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"trainer_config.json not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))

def _get_paths(cfg: dict) -> tuple[str, str, str, str, str]:
    datasets_dir  = cfg["datasets_dir"]
    dataset_file  = cfg.get("dataset_file", "combined_dataset.jsonl")
    DATASET_PATH  = os.path.join(datasets_dir, dataset_file)
    TRAIN_PATH    = os.path.join(datasets_dir, "train.jsonl")
    EVAL_PATH     = os.path.join(datasets_dir, "eval.jsonl")
    VALID_PATH    = os.path.join(datasets_dir, "valid.jsonl")
    REJECTED_PATH = os.path.join(datasets_dir, "rejected.jsonl")
    return DATASET_PATH, TRAIN_PATH, EVAL_PATH, VALID_PATH, REJECTED_PATH

REQUIRED_KEYS = {"id", "system", "prompt", "completion"}
EVAL_RATIO    = 0.05  # 95/5 split


def validate_and_load(path: str) -> tuple[list[dict], list[tuple[int, str]], list[dict]]:
    entries  = []
    errors   = []
    rejected = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append((i, f"JSON parse error: {e}"))
                rejected.append({"line": i, "reason": f"JSON parse error: {e}", "raw": line})
                continue
            missing = REQUIRED_KEYS - set(obj.keys())
            if missing:
                errors.append((i, f"Missing keys: {missing}"))
                rejected.append({"line": i, "reason": f"Missing keys: {missing}", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                continue
            for key in ("prompt", "completion"):
                if not isinstance(obj[key], str) or not obj[key].strip():
                    errors.append((i, f"Empty or non-string field: {key}"))
                    rejected.append({"line": i, "reason": f"Empty field: {key}", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                    break
            else:
                entries.append(obj)
    return entries, errors, rejected


def split(entries: list[dict], eval_ratio: float) -> tuple[list[dict], list[dict]]:
    data = entries.copy()
    random.seed(42)
    random.shuffle(data)
    eval_count = max(1, int(len(data) * eval_ratio))
    return data[eval_count:], data[:eval_count]


def _format_text(entry: dict) -> str:
    """Format entry as mlx_lm compatible text field."""
    system = entry.get("system", "").strip()
    prompt = entry.get("prompt", "").strip()
    completion = entry.get("completion", "").strip()
    if system:
        return f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{prompt} [/INST] {completion} </s>"
    return f"<s>[INST] {prompt} [/INST] {completion} </s>"

def write_jsonl(path: str, entries: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            out = dict(entry)
            out["text"] = _format_text(entry)
            f.write(json.dumps(out, ensure_ascii=False) + "\n")


def build() -> dict:
    cfg = _load_config()
    DATASET_PATH, TRAIN_PATH, EVAL_PATH, VALID_PATH, REJECTED_PATH = _get_paths(cfg)

    print(f"[dataset_builder] Loading: {DATASET_PATH}")
    entries, errors, rejected = validate_and_load(DATASET_PATH)

    print(f"[dataset_builder] Loaded:  {len(entries):,} valid entries")
    if errors:
        print(f"[dataset_builder] ERRORS:  {len(errors)} malformed entries")
        for lineno, msg in errors[:20]:
            print(f"  line {lineno}: {msg}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
    else:
        print("[dataset_builder] Validation: CLEAN — no errors")

    train, eval_ = split(entries, EVAL_RATIO)
    print(f"[dataset_builder] Split:   {len(train):,} train / {len(eval_):,} eval ({int(EVAL_RATIO*100)}% eval)")

    write_jsonl(TRAIN_PATH, train)
    write_jsonl(EVAL_PATH, eval_)
    write_jsonl(VALID_PATH, eval_)
    print(f"[dataset_builder] Written: {TRAIN_PATH}")
    print(f"[dataset_builder] Written: {EVAL_PATH} + valid.jsonl (mlx_lm alias)")

    write_jsonl(REJECTED_PATH, rejected)
    print(f"[dataset_builder] Written: {REJECTED_PATH} ({len(rejected)} rejected entries)")

    return {
        "total": len(entries) + len(errors),
        "valid": len(entries),
        "errors": len(errors),
        "train": len(train),
        "eval": len(eval_),
        "rejected": len(rejected),
        "train_path": TRAIN_PATH,
        "eval_path": EVAL_PATH,
    }


if __name__ == "__main__":
    result = build()
    print(f"\n[dataset_builder] Done. {result}")
