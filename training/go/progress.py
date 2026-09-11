"""Plain-text training reports; formatting never changes metric selection or data."""
from __future__ import annotations

from collections.abc import Mapping


def duration(seconds: float) -> str:
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def training_line(main: int, main_total: int, focus: int, focus_total: int,
                  losses: Mapping[str, float], windows: int, elapsed: float) -> str:
    completed, total = main + focus, main_total + focus_total
    eta = elapsed / max(1, completed) * (total - completed)
    rate = windows / max(elapsed, 1e-9)
    return (f"  main {main:>4}/{main_total} focus {focus:>3}/{focus_total} "
            f"loss={losses['total']:.4f} boundary_loss={losses['boundary']:.4f} "
            f"type_loss={losses['token_type']:.4f} modifier_loss={losses['modifier']:.4f} "
            f"{rate:.1f} win/s ETA={duration(eta)}")


def validation_line(split: str, step: int, total: int, windows: int, elapsed: float) -> str:
    eta = elapsed / max(1, step) * (total - step)
    return (f"  {split} {step:>4}/{total} batches "
            f"{windows / max(elapsed, 1e-9):.1f} win/s "
            f"elapsed={duration(elapsed)} ETA={duration(eta)}")


def modifier_micro_f1(diagnostics: Mapping) -> float:
    """Aggregate existing Gold-beginning counts; do not invent an end-to-end score."""
    counts = diagnostics['modifiersAtGoldBeginnings'].values()
    tp = fp = fn = 0
    for row in counts:
        tp += row['tp']
        fp += row['fp']
        fn += row['fn']
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0


def epoch_report(trained: Mapping, validation: Mapping, state: Mapping,
                 *, epoch_seconds: float, checkpoint_seconds: float,
                 remaining_epochs: int, mean_epoch_seconds: float,
                 patience: int, improved: bool, smoke: bool) -> str:
    main = trained['natural']['batchMeanLoss']
    focus = trained['focus']['batchMeanLoss']
    lines = ['', '  Training losses (lower is better; epoch batch means)']

    def add(label: str, value: str) -> None:
        lines.append(f"  {label + ':':<28} {value}")

    add('train loss', f"{main['total']:.4f}")
    add('boundary loss', f"{main['boundary']:.4f}")
    add('token type loss', f"{main['token_type']:.4f}")
    add('modifier loss', f"{main['modifier']:.4f}")
    add('focus loss', f"{focus['total']:.4f} ({trained['focus']['batches']} steps)")
    scope = 'complete-document smoke subset; not a benchmark' if smoke else 'full validation; higher F1 is better'
    for stream, title in [('natural', 'Natural validation'), ('focus', 'Focused validation')]:
        metrics = validation['streams'][stream]
        diagnostics = metrics['diagnostics']
        exact = metrics['exactSpan']
        lines.extend(['', f"  {title} ({scope})"])
        add('documents / windows', f"{metrics['documents']} / {metrics['windows']}")
        add('boundary macro F1', f"{diagnostics['boundary']['macroF1']:.4f}")
        add('token type macro F1', f"{diagnostics['tokenTypeAtGoldPositions']['macroF1']:.4f}")
        add('exact span F1', f"{exact['f1']:.4f}")
        add('exact span macro F1', f"{metrics['exactSpanMacroF1']:.4f}")
        add('predicted/gold spans', f"{exact['tp'] + exact['fp']}/{exact['tp'] + exact['fn']}")
        add('modifier F1 (Gold starts)', f"{modifier_micro_f1(diagnostics):.4f}")
    lines.extend(['', '  Timing (epoch time includes training, validation, and checkpoint saving)'])
    add('train time', duration(trained['seconds']))
    add('validation time', duration(validation['seconds']))
    add('checkpoint time', duration(checkpoint_seconds))
    add('epoch time', duration(epoch_seconds))
    add('remaining in this run', f"{remaining_epochs} epoch(s)")
    if remaining_epochs:
        add('run ETA', f"~{duration(mean_epoch_seconds * remaining_epochs)} (measured epoch average; estimate)")
    else:
        add('run ETA', '00:00')
    lines.append('')
    add('best natural exact span F1', f"{state['bestScore']:.4f} (epoch {state['bestEpoch']})")
    add('checkpoint selection', 'natural exact span F1; unchanged')
    if patience:
        add('early-stopping patience', f"{state['epochsWithoutImprovement']}/{patience} without improvement")
    else:
        add('early stopping', 'disabled')
    if improved:
        lines.append('  New best checkpoint saved.')
    return '\n'.join(lines)
