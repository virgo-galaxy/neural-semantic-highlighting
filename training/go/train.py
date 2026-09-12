"""Train a 512-byte Go baseline from an existing prepared snapshot."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
import shlex
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
from progress import epoch_report, training_line
from quality import targeted_gate_summary
from trainer_data import Snapshot, WindowSplit, epoch_batches, sha256_file, training_weights


@dataclass(frozen=True)
class TrainingConfig:
    batch_size: int = 32
    focus_batch_size: int = 16
    focus_every: int = 8
    focus_sampling: str = "feature-balanced"
    focus_features: str = ""
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
        if self.focus_sampling not in {"feature-balanced", "window-uniform"}:
            raise ValueError("Unknown focused sampling strategy")
        if self.focus_features and self.focus_sampling != "feature-balanced":
            raise ValueError("Focused feature filtering requires feature-balanced sampling")
        if self.patience < 0 or self.learning_rate <= 0 or self.weight_decay < 0 or self.modifier_loss_weight < 0:
            raise ValueError("Invalid optimizer or early-stopping configuration")
        if not all(math.isfinite(v) for v in (self.learning_rate, self.weight_decay, self.modifier_loss_weight, self.modifier_threshold)):
            raise ValueError("Non-finite training parameter")
        if not 0 < self.modifier_threshold < 1:
            raise ValueError("Invalid modifier threshold")


DEFAULT_EPOCHS = 3


def make_config(args: argparse.Namespace, checkpoint: dict | None) -> TrainingConfig:
    if checkpoint:
        saved = checkpoint["trainingConfig"].copy()
        # Checkpoints created before feature-balanced sampling must replay their
        # original window-uniform focused schedule when resumed.
        saved.setdefault("focus_sampling", "window-uniform")
    else:
        saved = asdict(TrainingConfig())
    values = saved.copy()
    for key in asdict(TrainingConfig()):
        value = getattr(args, key, None)
        if value is not None:
            if checkpoint and value != saved.get(key, getattr(TrainingConfig(), key)):
                raise ValueError(f"Resume must preserve {key}={saved.get(key)!r}; use a new run for a different training setup")
            values[key] = value
    config = TrainingConfig(**values)
    config.validate()
    return config


def epoch_train(model: GoSemanticTransformer, split: WindowSplit, optimizer: torch.optim.Optimizer,
                weights: dict, config: TrainingConfig, epoch: int, device: torch.device, log_every: int) -> dict:
    schedule = epoch_batches(split, batch_size=config.batch_size, focus_batch_size=config.focus_batch_size,
                             focus_every=config.focus_every, seed=config.seed, epoch=epoch,
                             max_main_batches=config.smoke_main_batches if config.smoke else 0,
                             focus_sampling=config.focus_sampling,
                             focus_features=tuple(value.strip() for value in config.focus_features.split(",") if value.strip()))
    totals = {kind: Counter() for kind in split.streams}
    steps = Counter(kind for kind, _ in schedule)
    completed = Counter()
    last_main_losses = None
    print("  Training losses (lower is better; latest main batch, not F1)", flush=True)
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
        completed[kind] += 1
        if kind == "natural":
            last_main_losses = parts
        if (step == 1 or step == len(schedule)
                or (kind == "natural" and completed["natural"] % log_every == 0)):
            elapsed = time.monotonic() - started
            print(training_line(completed["natural"], steps["natural"], completed["focus"], steps["focus"],
                                last_main_losses, sum(v["windows"] for v in totals.values()), elapsed), flush=True)
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
    if args.resume and args.init_from:
        raise ValueError("Use either --resume or --init-from, not both")
    checkpoint = load_checkpoint(args.resume) if args.resume else None
    init_checkpoint = load_checkpoint(args.init_from) if args.init_from else None
    config = make_config(args, checkpoint)
    epochs = args.epochs if args.epochs is not None else (1 if config.smoke else DEFAULT_EPOCHS)
    if epochs < 1 or args.log_every < 1:
        raise ValueError("Epochs and log interval must be positive")
    snapshot_arg = args.snapshot
    if checkpoint and snapshot_arg is None:
        # Resume the saved snapshot, not whichever current.json now points to.
        snapshot_arg = Path(checkpoint["snapshotPath"])
    snapshot = Snapshot.open(snapshot_arg)
    if checkpoint and (checkpoint["dataset"] != snapshot.identity() or checkpoint["schema"] != snapshot.schema):
        raise ValueError("Resume checkpoint snapshot/hash/schema does not match these prepared data")
    if init_checkpoint and init_checkpoint["schema"] != snapshot.schema:
        raise ValueError("Initialization checkpoint schema does not match these prepared data")
    device = select_device(args.device)
    seed_all(config.seed)
    torch_threads = args.cpu_threads
    if torch_threads is not None:
        if torch_threads < 1:
            raise ValueError("CPU thread count must be positive")
        torch.set_num_threads(torch_threads)
    elif device.type == "cpu":
        torch.set_num_threads(min(torch.get_num_threads(), 8))
    print("Neural Semantic Highlighting\nGo Multitask Training", flush=True)
    if config.smoke:
        print("SMOKE: pipeline verification, not a quality benchmark", flush=True)
    print(f"Epoch budget: {epochs} additional epoch(s) in this invocation", flush=True)
    print(f"Early stopping: {config.patience} epochs without natural exact-span F1 improvement"
          if config.patience else "Early stopping: disabled", flush=True)
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
        lineage = None
        if checkpoint:
            directory = args.resume.expanduser().resolve().parent
            if args.output_dir is not None and args.output_dir.expanduser().resolve() != directory:
                raise ValueError("Resume in the checkpoint run directory; do not fork a run implicitly")
            if args.resume.name != "last.pt":
                raise ValueError("Resume uses last.pt. best.pt is for inference/evaluation, not rewinding this run.")
            model = model_from_checkpoint(checkpoint, device)
            start_epoch, state = checkpoint["epoch"], checkpoint["trainingState"].copy()
            stored_weights = checkpoint["lossWeights"]
            print(f"Resume checkpoint: {args.resume.expanduser().resolve()}", flush=True)
            print(f"Completed epochs: {start_epoch}; next epoch: {start_epoch + 1}", flush=True)
        elif init_checkpoint:
            model = model_from_checkpoint(init_checkpoint, device)
            if model.config.context_bytes != snapshot.manifest["contextBytes"]:
                raise ValueError("Initialization checkpoint model context and dataset context do not match")
            start_epoch = 0
            state = {"bestScore": -1.0, "bestEpoch": 0, "epochsWithoutImprovement": 0, "optimizerSteps": 0}
            print("Counting new-snapshot training-only label frequencies for capped loss weights ...", flush=True)
            stored_weights = training_weights(train_split)
            directory = _fresh_directory(args.output_dir, config.smoke)
            lineage = {
                "mode": "weights-only-transfer",
                "checkpoint": str(args.init_from.expanduser().resolve()),
                "checkpointHash": sha256_file(args.init_from.expanduser().resolve()),
                "sourceEpoch": init_checkpoint["epoch"],
                "sourceDataset": init_checkpoint["dataset"],
            }
            print(f"Initialized weights from: {args.init_from.expanduser().resolve()}", flush=True)
            print("Optimizer/RNG/training state: fresh for the new dataset snapshot", flush=True)
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
                print("Optimizer state: restored; continuing existing weights, not restarting", flush=True)
            else:
                print("Checkpoint has no optimizer state; continuing with a fresh AdamW optimizer.", flush=True)
            restore_rng(checkpoint["rng"], device)
        print(f"Parameters: {parameter_count(model):,} | Context: {model.config.context_bytes} UTF-8 bytes", flush=True)
        print(f"Batch: {config.batch_size} natural / {config.focus_batch_size} focus; one focus batch per "
              f"{config.focus_every} natural batches (plus the final partial interval).", flush=True)
        if config.focus_sampling == "feature-balanced":
            selected = tuple(value.strip() for value in config.focus_features.split(",") if value.strip())
            if selected:
                missing = [feature for feature in selected if feature not in train_split.focus_feature_families]
                if missing:
                    raise ValueError(f"Unknown focused feature(s): {', '.join(missing)}")
                families = sum(len(train_split.focus_feature_families[value]) for value in selected)
                print(f"Focused sampling: feature-balanced across selected features {', '.join(selected)} / "
                      f"{families} feature-family buckets.", flush=True)
            else:
                families = sum(len(value) for value in train_split.focus_feature_families.values())
                print(f"Focused sampling: feature-balanced across {len(train_split.focus_feature_families)} features / "
                      f"{families} feature-family buckets.", flush=True)
        else:
            print("Focused sampling: window-uniform (legacy checkpoint replay).", flush=True)
        main_steps = math.ceil(len(train_split.streams["natural"]) / config.batch_size)
        if config.smoke:
            main_steps = min(main_steps, config.smoke_main_batches)
        focus_steps = math.ceil(main_steps / config.focus_every)
        print(f"Optimizer steps/epoch: {main_steps + focus_steps} ({main_steps} main + {focus_steps} focus)", flush=True)
        print(f"Planned optimizer steps: {(main_steps + focus_steps) * epochs}", flush=True)
        print(f"Planned epochs: {start_epoch + 1}..{start_epoch + epochs} (run 1/{epochs}..{epochs}/{epochs})", flush=True)
        print("Run ETA: awaiting the first complete epoch (training + validation + checkpoint saving)", flush=True)
        print("Loss: lower is better. Validation F1: higher is better. Loss 0.3 is not F1 0.3.", flush=True)
        print(f"Artifacts: {directory}", flush=True)
        with training_lock(directory):
            if not checkpoint:
                atomic_json(directory / "run.json", {
                    "format": "nsh-go-training-run-v1", "dataset": snapshot.identity(), "snapshotPath": str(snapshot.path),
                    "schema": snapshot.schema, "model": model.config.to_dict(), "training": asdict(config),
                    "device": device.type, "torchVersion": str(torch.__version__), "initialEpochBudget": epochs,
                    "lineage": lineage,
                    "trainerFiles": {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))
                                     if p.name not in {"prepare.py", "repair.py", "splitting.py"}},
                    "selection": "validation natural whole-document exact-span F1; fixed-window inference; excludes modifiers",
                })
            last = directory / "last.pt"
            measured_epochs = []
            for local_epoch, epoch in enumerate(range(start_epoch + 1, start_epoch + epochs + 1), 1):
                epoch_started = time.monotonic()
                print(f"\nEpoch {epoch} (run {local_epoch}/{epochs})", flush=True)
                trained = epoch_train(model, train_split, optimizer, weights, config, epoch, device, args.log_every)
                print("  validating... (complete documents; fixed-window inference)", flush=True)
                validation = evaluate_fixed(model, val_split, device, batch_size=config.batch_size,
                                            threshold=config.modifier_threshold, log_every=args.log_every,
                                            max_windows_per_stream=config.smoke_eval_windows if config.smoke else 0)
                validation["targetedRoleGate"] = targeted_gate_summary(validation)
                score = validation["streams"]["natural"]["exactSpan"]["f1"]
                improved = score > state["bestScore"] + 1e-9
                if improved:
                    state.update(bestScore=score, bestEpoch=epoch, epochsWithoutImprovement=0)
                else:
                    state["epochsWithoutImprovement"] += 1
                state["optimizerSteps"] += sum(trained[k]["batches"] for k in ("natural", "focus"))
                record = {"epoch": epoch, "runEpoch": local_epoch, "runEpochBudget": epochs,
                          "training": trained, "validation": validation, "trainingState": state.copy()}
                payload = {"format": FORMAT, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                           "epoch": epoch, "trainingState": state.copy(), "modelConfig": model.config.to_dict(),
                           "trainingConfig": asdict(config), "schema": snapshot.schema, "dataset": snapshot.identity(),
                           "snapshotPath": str(snapshot.path), "lossWeights": stored_weights, "rng": capture_rng(device),
                           "validation": validation, "torchVersion": str(torch.__version__)}
                checkpoint_started = time.monotonic()
                if improved:
                    save_checkpoint(directory / "best.pt", payload)
                save_checkpoint(last, payload)
                checkpoint_seconds = time.monotonic() - checkpoint_started
                epoch_seconds = time.monotonic() - epoch_started
                measured_epochs.append(epoch_seconds)
                stopping = bool(config.patience and state["epochsWithoutImprovement"] >= config.patience)
                remaining = 0 if stopping else epochs - local_epoch
                record["timing"] = {"epochSeconds": epoch_seconds, "checkpointSeconds": checkpoint_seconds}
                atomic_json(directory / "epochs" / f"epoch-{epoch:04d}.json", record)
                print(epoch_report(trained, validation, state, epoch_seconds=epoch_seconds,
                                   checkpoint_seconds=checkpoint_seconds, remaining_epochs=remaining,
                                   mean_epoch_seconds=sum(measured_epochs) / len(measured_epochs),
                                   patience=config.patience, improved=improved, smoke=config.smoke), flush=True)
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
            print(f"\nRun complete: {directory}", flush=True)
            print(f"Completed {len(measured_epochs)}/{epochs} requested epoch(s); last epoch: {epoch}.", flush=True)
            if not config.smoke:
                print("Review this short run before extending it; completing the budget is not a quality guarantee.", flush=True)
                print(f"Continue: make continue-go GO_CHECKPOINT={shlex.quote(str(last))} GO_EPOCHS={DEFAULT_EPOCHS}", flush=True)
            return directory
    finally:
        train_split.close()
        if val_split is not None:
            val_split.close()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--snapshot", type=Path, help="Snapshot directory or current.json; resume defaults to its saved snapshot")
    result.add_argument("--output-dir", type=Path, help="Empty output directory; default is a new timestamped artifacts/go run")
    result.add_argument("--resume", type=Path, help="Resume a last.pt on the exact saved dataset snapshot")
    result.add_argument("--init-from", type=Path, help="Initialize model weights from a Go checkpoint on a new dataset snapshot; optimizer/RNG are fresh")
    result.add_argument("--epochs", type=int, help="Additional epochs; default 1 for smoke and 3 otherwise")
    result.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    result.add_argument("--cpu-threads", type=int)
    result.add_argument("--log-every", type=int, default=25)
    result.add_argument("--smoke", action="store_true", default=None)
    result.add_argument("--focus-sampling", choices=["feature-balanced", "window-uniform"], default=None)
    result.add_argument("--focus-features", default=None, help="Comma-separated focused features for a targeted short run")
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
