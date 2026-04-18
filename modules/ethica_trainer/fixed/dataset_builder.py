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

# Quality thresholds — entries outside these are rejected
MIN_PROMPT_LEN     = 20    # chars
MIN_COMPLETION_LEN = 50    # chars
MAX_COMPLETION_LEN = 3000  # chars


def validate_and_load(path: str) -> tuple[list[dict], list[tuple[int, str]], list[dict]]:
    entries  = []
    errors   = []
    rejected = []
    seen_hashes: set[int] = set()  # deduplication
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
            fail = False
            for key in ("prompt", "completion"):
                if not isinstance(obj[key], str) or not obj[key].strip():
                    errors.append((i, f"Empty or non-string field: {key}"))
                    rejected.append({"line": i, "reason": f"Empty field: {key}", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                    fail = True
                    break
            if fail:
                continue

            # Quality gate
            prompt_len     = len(obj["prompt"].strip())
            completion_len = len(obj["completion"].strip())
            if prompt_len < MIN_PROMPT_LEN:
                rejected.append({"line": i, "reason": f"Prompt too short ({prompt_len} chars)", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                continue
            if completion_len < MIN_COMPLETION_LEN:
                rejected.append({"line": i, "reason": f"Completion too short ({completion_len} chars)", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                continue
            if completion_len > MAX_COMPLETION_LEN:
                rejected.append({"line": i, "reason": f"Completion too long ({completion_len} chars)", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                continue

            # Deduplication — hash on prompt+completion
            dedup_key = hash(obj["prompt"].strip() + obj["completion"].strip())
            if dedup_key in seen_hashes:
                rejected.append({"line": i, "reason": "Duplicate entry", "id": obj.get("id", ""), "prompt": obj.get("prompt", "")[:80]})
                continue
            seen_hashes.add(dedup_key)

            entries.append(obj)
    return entries, errors, rejected


def split(entries: list[dict], eval_ratio: float) -> tuple[list[dict], list[dict]]:
    data = entries.copy()
    random.seed(42)
    random.shuffle(data)
    eval_count = max(1, int(len(data) * eval_ratio))
    return data[eval_count:], data[:eval_count]


def _format_text(entry: dict) -> str:
    """Format entry as Mistral-correct chat template for mlx_lm."""
    system = entry.get("system", "").strip()
    prompt = entry.get("prompt", "").strip()
    completion = entry.get("completion", "").strip()
    # Mistral format: system prepended to first user turn, no <<SYS>> tokens
    user_turn = f"{system}\n\n{prompt}" if system else prompt
    return f"<s>[INST] {user_turn} [/INST] {completion}</s>"

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

    # Quality stats
    if entries:
        prompt_lens     = [len(e["prompt"]) for e in entries]
        completion_lens = [len(e["completion"]) for e in entries]
        print(f"[dataset_builder] Prompt     len — min:{min(prompt_lens):,}  avg:{int(sum(prompt_lens)/len(prompt_lens)):,}  max:{max(prompt_lens):,}")
        print(f"[dataset_builder] Completion len — min:{min(completion_lens):,}  avg:{int(sum(completion_lens)/len(completion_lens)):,}  max:{max(completion_lens):,}")
        dupes_caught = len([r for r in rejected if r.get("reason") == "Duplicate entry"])
        print(f"[dataset_builder] Duplicates removed: {dupes_caught:,}")

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
