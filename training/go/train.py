"""Train a 512-byte Go baseline from an existing prepared snapshot."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import sys
import time

import torch

from checkpoints import (FORMAT, atomic_json, capture_rng, load_checkpoint, model_from_checkpoint,
                         restore_rng, save_checkpoint, seed_all, select_device, training_lock)
from inference import decode, document_logits
from losses import compute_loss
from metrics import evaluate_fixed, evaluation_indices
from model import GoSemanticTransformer, ModelConfig, parameter_count
from trainer_data import Snapshot, WindowSplit, epoch_batches, sha256_file, training_weights


@dataclass(frozen=True)
class TrainingConfig:
    batch_size: int = 32
    focus_batch_size: int = 16
    focus_every: int = 8
    learning_rate: float = 3e-4
    weight_decay: float = .01
    modifier_loss_weight: float = .1
    modifier_threshold: float = .60
    seed: int = 42
    patience: int = 5
    smoke: bool = False
    smoke_main_batches: int = 8
    smoke_eval_windows: int = 24

    def validate(self) -> None:
        if min(self.batch_size, self.focus_batch_size, self.focus_every, self.smoke_main_batches, self.smoke_eval_windows) < 1:
            raise ValueError("Batch sizes, sampling interval, and smoke limits must be positive")
        if self.patience < 0 or self.learning_rate <= 0 or self.weight_decay < 0 or self.modifier_loss_weight < 0:
            raise ValueError("Invalid optimizer or early-stopping configuration")
        if not all(math.isfinite(v) for v in (self.learning_rate, self.weight_decay, self.modifier_loss_weight, self.modifier_threshold)):
            raise ValueError("Non-finite training parameter")
        if not 0 < self.modifier_threshold < 1:
            raise ValueError("Invalid modifier threshold")


def duration(seconds: float) -> str:
    minutes, sec = divmod(max(0, int(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def make_config(args: argparse.Namespace, checkpoint: dict | None) -> TrainingConfig:
    saved = checkpoint["trainingConfig"] if checkpoint else asdict(TrainingConfig())
    values = saved.copy()
    for key in values:
        value = getattr(args, key, None)
        if value is not None:
            if checkpoint and value != saved[key]:
                raise ValueError(f"Resume must preserve {key}={saved[key]!r}; use a new run for a different training setup")
            values[key] = value
    config = TrainingConfig(**values)
    config.validate()
    return config


def epoch_train(model: GoSemanticTransformer, split: WindowSplit, optimizer: torch.optim.Optimizer,
                weights: dict, config: TrainingConfig, epoch: int, device: torch.device, log_every: int) -> dict:
    schedule = epoch_batches(split, batch_size=config.batch_size, focus_batch_size=config.focus_batch_size,
                             focus_every=config.focus_every, seed=config.seed, epoch=epoch,
                             max_main_batches=config.smoke_main_batches if config.smoke else 0)
    totals = {kind: Counter() for kind in split.streams}
    steps = Counter(kind for kind, _ in schedule)
    print(f"Epoch {epoch}: {steps['natural']} natural + {steps['focus']} focused batches", flush=True)
    started = time.monotonic()
    model.train()
    for step, (kind, indices) in enumerate(schedule, 1):
        batch = split.batch(indices, device)
        optimizer.zero_grad(set_to_none=True)
        output = model(batch["input_ids"], batch["attention_mask"])
        loss, parts = compute_loss(output, batch, weights, config.modifier_loss_weight)
        if not bool(torch.isfinite(loss)):
            raise ValueError(f"Non-finite loss at epoch {epoch}, step {step}; checkpoint not advanced")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0, error_if_nonfinite=True)
        optimizer.step()
        totals[kind].update(parts)
        totals[kind].update(batches=1, windows=len(indices))
        if step == 1 or step % log_every == 0 or step == len(schedule):
            elapsed = time.monotonic() - started
            eta = elapsed / step * (len(schedule) - step)
            print(f"  step {step}/{len(schedule)} [{kind}] loss={parts['total']:.4f} "
                  f"boundary={parts['boundary']:.4f} type={parts['token_type']:.4f} modifier={parts['modifier']:.4f} "
                  f"elapsed={duration(elapsed)} eta={duration(eta)}", flush=True)
    result = {}
    for kind, values in totals.items():
        result[kind] = {"batches": int(values["batches"]), "windowPresentations": int(values["windows"]),
                        "batchMeanLoss": {key: values[key] / max(1, values["batches"])
                                          for key in ("total", "boundary", "token_type", "modifier")}}
    result["seconds"] = time.monotonic() - started
    return result


def _fresh_directory(path: Path | None, smoke: bool) -> Path:
    if path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        path = Path("artifacts/go") / (("smoke-" if smoke else "context512-") + stamp)
    path = path.expanduser().resolve()
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Output directory is not empty: {path}. Resume explicitly or choose a new path.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(args: argparse.Namespace, *, model_config: ModelConfig | None = None) -> Path:
    checkpoint = load_checkpoint(args.resume) if args.resume else None
    config = make_config(args, checkpoint)
    epochs = args.epochs if args.epochs is not None else (1 if config.smoke else 32)
    if epochs < 1 or args.log_every < 1:
        raise ValueError("Epochs and log interval must be positive")
    snapshot_arg = args.snapshot
    if checkpoint and snapshot_arg is None:
        # Resume the saved snapshot, not whichever current.json now points to.
        snapshot_arg = Path(checkpoint["snapshotPath"])
    snapshot = Snapshot.open(snapshot_arg)
    if checkpoint and (checkpoint["dataset"] != snapshot.identity() or checkpoint["schema"] != snapshot.schema):
        raise ValueError("Resume checkpoint snapshot/hash/schema does not match these prepared data")
    device = select_device(args.device)
    seed_all(config.seed)
    torch_threads = args.cpu_threads
    if torch_threads is not None:
        if torch_threads < 1:
            raise ValueError("CPU thread count must be positive")
        torch.set_num_threads(torch_threads)
    elif device.type == "cpu":
        torch.set_num_threads(min(torch.get_num_threads(), 8))
    print("Go Semantic Transformer" + (" [SMOKE: pipeline verification, not a quality benchmark]" if config.smoke else ""), flush=True)
    print(f"Snapshot: {snapshot.manifest['snapshot'][:20]} | Device: {device} | PyTorch: {torch.__version__}", flush=True)
    print("Verifying train and validation checksums; the test split is not opened.", flush=True)
    train_split = WindowSplit(snapshot, "train")
    val_split = None
    try:
        val_split = WindowSplit(snapshot, "validation")
        for name, split in (("train", train_split), ("validation", val_split)):
            if any(not ids for ids in split.streams.values()):
                raise ValueError(f"Both streams are required in {name}")
            print(f"{name}: {len(split.streams['natural'])} natural + {len(split.streams['focus'])} focus windows", flush=True)
        if checkpoint:
            directory = args.resume.expanduser().resolve().parent
            if args.output_dir is not None and args.output_dir.expanduser().resolve() != directory:
                raise ValueError("Resume in the checkpoint run directory; do not fork a run implicitly")
            if args.resume.name != "last.pt":
                raise ValueError("Resume uses last.pt. best.pt is for inference/evaluation, not rewinding this run.")
            model = model_from_checkpoint(checkpoint, device)
            start_epoch, state = checkpoint["epoch"], checkpoint["trainingState"].copy()
            stored_weights = checkpoint["lossWeights"]
        else:
            model = GoSemanticTransformer(model_config or ModelConfig(), len(snapshot.schema["tokenTypes"]),
                                          len(snapshot.schema["modifiers"])).to(device)
            if model.config.context_bytes != snapshot.manifest["contextBytes"]:
                raise ValueError("Model context and dataset context do not match")
            start_epoch = 0
            state = {"bestScore": -1.0, "bestEpoch": 0, "epochsWithoutImprovement": 0, "optimizerSteps": 0}
            print("Counting training-only label frequencies for capped loss weights ...", flush=True)
            stored_weights = training_weights(train_split)
            directory = _fresh_directory(args.output_dir, config.smoke)
        weights = {key: value.to(device) for key, value in stored_weights.items()}
        optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        if checkpoint:
            if checkpoint.get("optimizer"):
                optimizer.load_state_dict(checkpoint["optimizer"])
            else:
                print("Checkpoint has no optimizer state; continuing with a fresh AdamW optimizer.", flush=True)
            restore_rng(checkpoint["rng"], device)
        print(f"Parameters: {parameter_count(model):,} | Context: {model.config.context_bytes} UTF-8 bytes", flush=True)
        print(f"Batch: {config.batch_size} natural / {config.focus_batch_size} focus; one focus batch per "
              f"{config.focus_every} natural batches (plus the final partial interval).", flush=True)
        print(f"Artifacts: {directory}", flush=True)
        with training_lock(directory):
            if not checkpoint:
                atomic_json(directory / "run.json", {
                    "format": "nsh-go-training-run-v1", "dataset": snapshot.identity(), "snapshotPath": str(snapshot.path),
                    "schema": snapshot.schema, "model": model.config.to_dict(), "training": asdict(config),
                    "device": device.type, "torchVersion": str(torch.__version__),
                    "trainerFiles": {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))
                                     if p.name not in {"prepare.py", "repair.py", "splitting.py"}},
                    "selection": "validation natural whole-document exact-span F1; fixed-window inference; excludes modifiers",
                })
            last = directory / "last.pt"
            for epoch in range(start_epoch + 1, start_epoch + epochs + 1):
                trained = epoch_train(model, train_split, optimizer, weights, config, epoch, device, args.log_every)
                print(f"Epoch {epoch}: validation (complete documents, fixed-window inference) ...", flush=True)
                validation = evaluate_fixed(model, val_split, device, batch_size=config.batch_size,
                                            threshold=config.modifier_threshold, log_every=args.log_every,
                                            max_windows_per_stream=config.smoke_eval_windows if config.smoke else 0)
                score = validation["streams"]["natural"]["exactSpan"]["f1"]
                improved = score > state["bestScore"] + 1e-9
                if improved:
                    state.update(bestScore=score, bestEpoch=epoch, epochsWithoutImprovement=0)
                else:
                    state["epochsWithoutImprovement"] += 1
                state["optimizerSteps"] += sum(trained[k]["batches"] for k in ("natural", "focus"))
                record = {"epoch": epoch, "training": trained, "validation": validation, "trainingState": state.copy()}
                payload = {"format": FORMAT, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                           "epoch": epoch, "trainingState": state.copy(), "modelConfig": model.config.to_dict(),
                           "trainingConfig": asdict(config), "schema": snapshot.schema, "dataset": snapshot.identity(),
                           "snapshotPath": str(snapshot.path), "lossWeights": stored_weights, "rng": capture_rng(device),
                           "validation": validation, "torchVersion": str(torch.__version__)}
                if improved:
                    save_checkpoint(directory / "best.pt", payload)
                save_checkpoint(last, payload)
                atomic_json(directory / "epochs" / f"epoch-{epoch:04d}.json", record)
                natural, focus = validation["streams"]["natural"], validation["streams"]["focus"]
                print(f"Epoch {epoch} complete | natural exact F1={score:.4f}, macro={natural['exactSpanMacroF1']:.4f} | "
                      f"focus exact F1={focus['exactSpan']['f1']:.4f} | best epoch={state['bestEpoch']}", flush=True)
                print(f"Saved: {last}", flush=True)
                if config.patience and state["epochsWithoutImprovement"] >= config.patience:
                    print(f"Early stopping: no natural validation improvement for {config.patience} epochs.", flush=True)
                    break
            if config.smoke:
                reloaded = load_checkpoint(last)
                loaded_model = model_from_checkpoint(reloaded, device)
                candidates = evaluation_indices(val_split, config.smoke_eval_windows)
                doc_id = val_split.refs[candidates[0]]["documentId"]
                doc = val_split.documents()[doc_id]
                before = document_logits(model, doc["source"], device)
                after = document_logits(loaded_model, doc["source"], device)
                for original, loaded in ((before.boundary, after.boundary), (before.token_type, after.token_type),
                                         (before.modifier, after.modifier)):
                    torch.testing.assert_close(original, loaded, atol=1e-5, rtol=1e-5)
                result = decode(doc["source"], after, snapshot.schema, threshold=config.modifier_threshold)
                # JSON prediction is intentionally a plain public HighlightResult.
                atomic_json(directory / "smoke-prediction.json", result)
                atomic_json(directory / "smoke-report.json", {
                    "checkpointReload": "passed", "adaptiveSourceInference": "passed", "documentId": doc_id,
                    "sourceBytes": len(doc["source"].encode("utf-8")), "predictedSpans": len(result["spans"]),
                    "optimizerSteps": state["optimizerSteps"], "qualityClaim": "none; smoke run only",
                })
                print("SMOKE PASS: optimizer updates, validation, checkpoint reload, and adaptive source inference.", flush=True)
                print("This smoke checkpoint is not a baseline-quality or selected model.", flush=True)
            print(f"Run complete: {directory}", flush=True)
            return directory
    finally:
        train_split.close()
        if val_split is not None:
            val_split.close()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--snapshot", type=Path, help="Snapshot directory or current.json; resume defaults to its saved snapshot")
    result.add_argument("--output-dir", type=Path, help="Empty output directory; default is a new timestamped artifacts/go run")
    result.add_argument("--resume", type=Path, help="Resume a last.pt; epochs are additional, not an absolute target")
    result.add_argument("--epochs", type=int, help="Additional epochs; default 1 for smoke and 32 otherwise")
    result.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    result.add_argument("--cpu-threads", type=int)
    result.add_argument("--log-every", type=int, default=25)
    result.add_argument("--smoke", action="store_true", default=None)
    for name in ("batch-size", "focus-batch-size", "focus-every", "seed", "patience", "smoke-main-batches", "smoke-eval-windows"):
        result.add_argument("--" + name, type=int, default=None)
    for name in ("learning-rate", "weight-decay", "modifier-loss-weight", "modifier-threshold"):
        result.add_argument("--" + name, type=float, default=None)
    return result


def main() -> int:
    try:
        run(parser().parse_args())
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted. Completed epoch checkpoints are preserved; the current partial epoch was not committed.", file=sys.stderr)
        return 130
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Go training failed: {error}", file=sys.stderr)
        if "out of memory" in str(error).lower():
            print("Use a smaller --batch-size / --focus-batch-size in a new run; no global settings were changed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
