"""Short, resumable pack experiments using the existing small-model architecture."""
from __future__ import annotations

from training.shared.spec import current

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import random
import subprocess
import time

import torch

from training.shared.checkpoints import (atomic_json, capture_rng, load_checkpoint,
    model_from_checkpoint, restore_rng, save_checkpoint, seed_all, select_device, training_lock)
from training.shared.inference import document_logits
from training.shared.initialization import initialize_from_checkpoint
from training.shared.losses import compute_loss
from training.shared.metrics import evaluate_fixed
from training.shared.model import SemanticTransformer, ModelConfig, parameter_count
from training.shared.prepare import REPOSITORY, file_hash
from training.shared.progress import duration, training_line
from training.shared.trainer_data import Snapshot, WindowSplit, training_weights
from training.shared.provenance import code_hashes



@dataclass(frozen=True)
class TrainingConfig:
    batch_size: int = 32
    learning_rate: float = .0003
    weight_decay: float = .01
    modifier_loss_weight: float = .1
    modifier_threshold: float = .60
    patience: int = 5
    seed: int = 42
    smoke: bool = False
    smoke_batches: int = 8
    smoke_eval_windows: int = 48
    sampling: str = "natural-plus-curriculum"
    focus_every: int = 1
    focus_batch_size: int = 16

    def validate(self):
        if min(self.batch_size, self.smoke_batches, self.smoke_eval_windows, self.focus_every, self.focus_batch_size) < 1 or self.patience < 0:
            raise ValueError("Invalid training budget")
        if (not all(math.isfinite(x) and x > 0 for x in (self.learning_rate, self.modifier_loss_weight))
                or not math.isfinite(self.weight_decay) or self.weight_decay < 0
                or not 0 < self.modifier_threshold < 1 or self.sampling not in {"shuffled-windows", "natural-plus-curriculum"}):
            raise ValueError("Invalid optimizer, decoder or sampler configuration")


def epoch_batches(split: WindowSplit, config: TrainingConfig, epoch: int) -> list[list[int]]:
    """Preserve natural coverage; rotate a bounded independently marked curriculum."""
    rng = random.Random(config.seed + epoch)
    natural = [i for i, ref in enumerate(split.refs) if ref.get("stream", "natural") == "natural"]
    focus = [i for i, ref in enumerate(split.refs) if ref.get("stream") == "focus"]
    if not natural: raise ValueError("Training needs real-source natural windows")
    if config.sampling == "shuffled-windows": natural, focus = list(range(len(split.refs))), []
    rng.shuffle(natural)
    main = [natural[start:start + config.batch_size] for start in range(0, len(natural), config.batch_size)]
    batches = []
    random.Random(config.seed).shuffle(focus)
    focus_steps = (len(main) + config.focus_every - 1) // config.focus_every
    cursor = (epoch - 1) * focus_steps * config.focus_batch_size
    for step, batch in enumerate(main, 1):
        batches.append(batch)
        if focus and (step % config.focus_every == 0 or step == len(main)):
            batches.append([focus[(cursor + i) % len(focus)] for i in range(config.focus_batch_size)])
            cursor += config.focus_batch_size
    return batches[:config.smoke_batches] if config.smoke else batches


def train_epoch(model, split, optimizer, weights, config, device, epoch, log_every):
    batches = epoch_batches(split, config, epoch)
    model.train()
    start, total, presented = time.monotonic(), 0., 0
    main_steps = sum(split.refs[b[0]].get("stream", "natural") == "natural" for b in batches)
    focus_steps = len(batches) - main_steps
    main_step = focus_step = natural_presented = focus_presented = 0
    for step, indices in enumerate(batches, 1):
        batch = split.batch(indices, device)
        optimizer.zero_grad(set_to_none=True)
        loss, parts = compute_loss(model(batch["input_ids"], batch["attention_mask"]), batch,
                                   weights, config.modifier_loss_weight)
        if not bool(torch.isfinite(loss)):
            raise ValueError("Non-finite loss; checkpoint was not advanced")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
        optimizer.step()
        total += parts["total"]
        presented += len(indices)
        if split.refs[indices[0]].get("stream", "natural") == "focus":
            focus_step += 1
            focus_presented += len(indices)
        else:
            main_step += 1
            natural_presented += len(indices)
        if step in (1, len(batches)) or step % log_every == 0:
            print(training_line(main_step, main_steps, focus_step, focus_steps, parts, presented, time.monotonic() - start), flush=True)
    return {"loss": total / len(batches), "seconds": time.monotonic() - start,
            "optimizerSteps": len(batches), "presentedWindows": presented,
            "naturalPresentations": natural_presented, "focusPresentations": focus_presented}


def selection_score(report: dict) -> float:
    values = [report["profiles"][profile]["natural"] for profile in current().profiles]
    if any(not value["documents"] for value in values):
        raise ValueError("Selection requires real-source natural validation for all pack profiles")
    return sum(value["exactSpanMacroF1"] for value in values) / len(values)


def run(args) -> Path:
    if args.epochs < 1 or args.log_every < 1:
        raise ValueError("Epoch and log budgets must be positive")
    if args.resume and args.init_from:
        raise ValueError("Use either --resume or --init-from, not both")
    if args.resume and (args.resume.name != "last.pt" or (args.output_dir is not None
            and args.output_dir.resolve() != args.resume.resolve().parent)):
        raise ValueError("Resume last.pt in its existing run directory; initialization starts a separate run")
    device = select_device(args.device)
    if device.type == "cpu":
        torch.set_num_threads(min(4, torch.get_num_threads()))
    checkpoint = load_checkpoint(args.resume.resolve()) if args.resume else None
    if checkpoint:current().verify_config(checkpoint.get('provenance',{}))
    values = checkpoint["trainingConfig"].copy() if checkpoint else asdict(TrainingConfig())
    for name in ("batch_size", "learning_rate", "patience", "smoke", "focus_batch_size", "focus_every"):
        value = getattr(args, name)
        if value is not None:
            if checkpoint and values[name] != value:
                raise ValueError("Resume must preserve training configuration: " + name)
            values[name] = value
    config = TrainingConfig(**values)
    config.validate()
    snapshot_path = args.snapshot
    if checkpoint:
        snapshot_path = snapshot_path or Path(checkpoint["dataset"]["path"])
    snapshot = Snapshot.open(snapshot_path)
    if checkpoint and snapshot.identity() != {key: checkpoint["dataset"][key] for key in ("snapshot", "manifestHash")}:
        raise ValueError("Resume dataset identity mismatch")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    directory = (args.output_dir or (args.resume.parent if args.resume else
        Path("artifacts") / current().id / (("smoke-" if config.smoke else "context512-") + stamp))).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    with training_lock(directory):
        fresh_directory = not checkpoint or args.resume.resolve().parent != directory
        if fresh_directory and any((directory / name).exists() for name in ("last.pt", "best.pt", "run.json")):
            raise ValueError("Existing run; resume its last.pt instead of overwriting it")
        seed_all(config.seed)
        local_kernel = args.local_kernel
        if checkpoint and local_kernel is not None and local_kernel != checkpoint["modelConfig"].get("local_kernel", 1):
            raise ValueError("Resume must preserve model configuration")
        model = model_from_checkpoint(checkpoint, device) if checkpoint else SemanticTransformer(
            ModelConfig(local_kernel=local_kernel or 1), len(snapshot.schema["tokenTypes"]), len(snapshot.schema["modifiers"])).to(device)
        initialization = checkpoint.get("initialization") if checkpoint else None
        if args.init_from:
            initialization = initialize_from_checkpoint(model, args.init_from)
        optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        state = checkpoint["trainingState"].copy() if checkpoint else {
            "bestScore": -1., "bestEpoch": 0, "epochsWithoutImprovement": 0, "optimizerSteps": 0}
        first_epoch = checkpoint["epoch"] + 1 if checkpoint else 1
        train = validation = None
        atomic_json(directory / "status.json", {"status": "preparing", "nextEpoch": first_epoch})
        try:
            train, validation = WindowSplit(snapshot, "train"), WindowSplit(snapshot, "validation")
            if checkpoint:
                weights = {name: value.to(device) for name, value in checkpoint["lossWeights"].items()}
                optimizer.load_state_dict(checkpoint["optimizer"])
                restore_rng(checkpoint["rng"], device)
            else:
                weights = {name: value.to(device) for name, value in training_weights(train).items()}
            provenance = {"codeHashes": code_hashes(),
                "semanticsHash": file_hash(current().semantics_path),
                "packConfigHash": file_hash(current().directory/'pack.json'),
                "decoderPolicy": current().decoder(),
                "pythonTorch": str(torch.__version__),
                "repositoryDirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPOSITORY, text=True)),
                "repositoryCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()}
            invocation = {"device": device.type, "initialEpochBudget": args.epochs, "trainingConfig": asdict(config),
                "modelConfig": model.config.to_dict(), "parameters": parameter_count(model),
                "dataset": {**snapshot.identity(), "path": str(snapshot.path)},
                "selection": "mean per-profile natural real-source validation exact-span macro F1; fixed-window logits reassembled",
                "initialization": initialization,
                "provenance": provenance, "resumeCheckpoint": str(args.resume) if args.resume else None}
            if not checkpoint:
                atomic_json(directory / "run.json", invocation)
            atomic_json(directory / "invocations" / (stamp + ".json"), invocation)
            print(f"pack neural training\nDevice: {device}; PyTorch: {torch.__version__}\n"
                  f"Parameters: {parameter_count(model):,}; context: 512 UTF-8 bytes\nRun: {directory}\n"
                  f"Epoch budget: {args.epochs} additional; range {first_epoch}..{first_epoch + args.epochs - 1}\n"
                  f"Batch size: {config.batch_size}; patience: {config.patience}; smoke: {config.smoke}\n"
                  f"Unique train windows: {len(train.refs)}; bounded curriculum is separate from real-source windows\n"
                  f"Optimizer steps/epoch: {len(epoch_batches(train, config, first_epoch))}", flush=True)
            timings = []
            for epoch in range(first_epoch, first_epoch + args.epochs):
                epoch_start = time.monotonic()
                atomic_json(directory / "status.json", {"status": "running", "epoch": epoch,
                    "completedEpoch": epoch - 1, "phase": "training"})
                print(f"\nEpoch {epoch} (run {epoch - first_epoch + 1}/{args.epochs})", flush=True)
                trained = train_epoch(model, train, optimizer, weights, config, device, epoch, args.log_every)
                atomic_json(directory / "status.json", {"status": "running", "epoch": epoch,
                    "completedEpoch": epoch - 1, "phase": "validation"})
                report = evaluate_fixed(model, validation, device, batch_size=config.batch_size,
                    threshold=config.modifier_threshold,
                    max_windows_per_stream=config.smoke_eval_windows if config.smoke else 0, log_every=args.log_every)
                score = selection_score(report)
                improved = score > state["bestScore"]
                state["optimizerSteps"] += trained["optimizerSteps"]
                if improved:
                    state.update(bestScore=score, bestEpoch=epoch, epochsWithoutImprovement=0)
                else:
                    state["epochsWithoutImprovement"] += 1
                payload = {"format": current().checkpoint_format, "epoch": epoch, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "rng": capture_rng(device), "modelConfig": model.config.to_dict(), "schema": snapshot.schema,
                    "dataset": invocation["dataset"], "trainingConfig": asdict(config), "trainingState": state.copy(),
                    "lossWeights": weights, "validation": report, "provenance": provenance, "documentKinds": list(current().document_kinds),
                    "initialization": initialization}
                checkpoint_start = time.monotonic()
                save_checkpoint(directory / "last.pt", payload)
                if improved:
                    save_checkpoint(directory / "best.pt", payload)
                seconds = time.monotonic() - epoch_start
                timings.append(seconds)
                atomic_json(directory / "epochs" / f"epoch-{epoch:04d}.json",
                    {"epoch": epoch, "training": trained, "validation": report, "trainingState": state,
                     "timing": {"epochSeconds": seconds, "checkpointSeconds": time.monotonic() - checkpoint_start}})
                for kind, metrics in report["documentKinds"].items():
                    print(f"  {kind:<4} validation: F1={metrics['exactSpan']['f1']:.4f} "
                          f"macro={metrics['exactSpanMacroF1']:.4f} documents={metrics['documents']}", flush=True)
                for stream, metrics in report["streams"].items():
                    if metrics["documents"]:
                        print(f"  {stream:<7}: F1={metrics['exactSpan']['f1']:.4f} macro={metrics['exactSpanMacroF1']:.4f} documents={metrics['documents']}", flush=True)
                remaining = first_epoch + args.epochs - epoch - 1
                print(f"  selection={score:.4f}; best={state['bestScore']:.4f} (epoch {state['bestEpoch']}); "
                      f"no improvement={state['epochsWithoutImprovement']}/{config.patience}\n"
                      f"  epoch time={duration(seconds)}; run ETA=~{duration(sum(timings) / len(timings) * remaining)}\n"
                      f"  Saved: {directory / 'last.pt'}", flush=True)
                atomic_json(directory / "status.json", {"status": "running", "completedEpoch": epoch,
                    "bestEpoch": state["bestEpoch"], "bestScore": state["bestScore"], "phase": "checkpoint-saved"})
                if config.patience and state["epochsWithoutImprovement"] >= config.patience:
                    print("Early stopping: validation selection score plateaued.", flush=True)
                    break
            if config.smoke:
                saved = load_checkpoint(directory / "last.pt")
                reloaded = model_from_checkpoint(saved, device)
                source = next(iter(validation.documents().values()))["source"]
                a = document_logits(model, source, device)
                b = document_logits(reloaded, source, device)
                for name in ("boundary", "token_type", "modifier"):
                    torch.testing.assert_close(getattr(a, name), getattr(b, name))
                print("SMOKE PASS: checkpoint reload and pure-neural document inference verified; not a quality claim.", flush=True)
            atomic_json(directory / "status.json", {"status": "completed", "completedEpoch": epoch,
                "bestEpoch": state["bestEpoch"], "bestScore": state["bestScore"], "smoke": config.smoke})
        except BaseException as error:
            atomic_json(directory / "status.json", {"status": "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                "error": str(error), "lastCheckpoint": str(directory / "last.pt")})
            raise
        finally:
            if train:
                train.close()
            if validation:
                validation.close()
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3, help="Additional completed epochs in this invocation")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--patience", type=int)
    parser.add_argument("--focus-batch-size", type=int)
    parser.add_argument("--focus-every", type=int)
    parser.add_argument("--local-kernel", type=int, choices=[1, 3, 5],
                        help="Fresh bounded experiment: optional learned adjacent-byte residual; default historical backbone")
    parser.add_argument("--smoke", action="store_true", default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--init-from", type=Path,
                        help="Compatible full training checkpoint for weights-only initialization of a fresh pack experiment")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--log-every", type=int, default=25)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
