"""Console regressions: familiar epoch reports, explicit loss/F1, and short runs."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoints import load_checkpoint
from model import ModelConfig
from progress import duration, epoch_report, modifier_micro_f1, training_line, validation_line
from train import DEFAULT_EPOCHS, TrainingConfig, parser, run
from test_trainer import synthetic_snapshot


class ProgressTests(unittest.TestCase):
    def test_duration_matches_compact_typescript_clock(self):
        self.assertEqual(duration(0), '00:00')
        self.assertEqual(duration(-1), '00:00')
        self.assertEqual(duration(273), '04:33')
        self.assertEqual(duration(3661), '01:01:01')

    def test_training_line_separates_losses_and_counts_both_streams(self):
        losses = {'total': .3, 'boundary': .1, 'token_type': .15, 'modifier': .5}
        line = training_line(8, 16, 1, 2, losses, 272, 9)
        self.assertIn('main    8/16 focus   1/2', line)
        self.assertIn('boundary_loss=0.1000', line)
        self.assertIn('modifier_loss=0.5000', line)
        self.assertIn('30.2 win/s ETA=00:09', line)
        self.assertNotIn('F1=', line)
        self.assertIn('ETA=00:00', training_line(16, 16, 2, 2, losses, 544, 18))

    def test_validation_progress_displays_elapsed_and_eta(self):
        self.assertEqual(validation_line('validation', 25, 100, 800, 20),
                         '  validation   25/100 batches 40.0 win/s elapsed=00:20 ETA=01:00')

    def test_modifier_aggregation_uses_raw_counts_not_average_f1(self):
        diagnostics = {'modifiersAtGoldBeginnings': {'one': {'tp': 9, 'fp': 0, 'fn': 1},
                                                    'two': {'tp': 1, 'fp': 2, 'fn': 3}}}
        self.assertAlmostEqual(modifier_micro_f1(diagnostics), 20 / 26)
        self.assertEqual(modifier_micro_f1({'modifiersAtGoldBeginnings': {}}), 0)

    @staticmethod
    def metrics():
        return {'documents': 2, 'windows': 3, 'exactSpan': {'f1': .6, 'tp': 3, 'fp': 2, 'fn': 2},
                'exactSpanMacroF1': .4, 'diagnostics': {'boundary': {'macroF1': .8},
                'tokenTypeAtGoldPositions': {'macroF1': .7},
                'modifiersAtGoldBeginnings': {'declaration': {'tp': 2, 'fp': 1, 'fn': 1}}}}

    def report(self, remaining=2, smoke=False):
        losses = {'total': .3, 'boundary': .1, 'token_type': .15, 'modifier': .5}
        trained = {'seconds': 6, 'natural': {'batchMeanLoss': losses, 'batches': 8},
                   'focus': {'batchMeanLoss': losses, 'batches': 1}}
        val = {'seconds': 3, 'streams': {'natural': self.metrics(), 'focus': self.metrics()}}
        state = {'bestScore': .6, 'bestEpoch': 1, 'epochsWithoutImprovement': 0}
        before = copy.deepcopy((trained, val, state))
        text = epoch_report(trained, val, state, epoch_seconds=10, checkpoint_seconds=1,
                            remaining_epochs=remaining, mean_epoch_seconds=10, patience=5,
                            improved=True, smoke=smoke)
        self.assertEqual((trained, val, state), before)
        return text

    def test_epoch_report_keeps_f1_and_loss_separate_with_two_streams(self):
        text = self.report()
        for name in ['train loss:', 'boundary loss:', 'token type loss:', 'modifier loss:',
                     'focus loss:', 'boundary macro F1:', 'token type macro F1:',
                     'exact span F1:', 'exact span macro F1:', 'predicted/gold spans:',
                     'modifier F1 (Gold starts):', 'Natural validation', 'Focused validation']:
            self.assertIn(name, text)
        self.assertIn('lower is better', text)
        self.assertIn('higher F1 is better', text)
        self.assertIn('5/5', text)
        self.assertIn('0.6667', text)
        self.assertIn('natural exact span F1; unchanged', text)

    def test_report_measures_complete_epoch_and_reports_remaining_budget(self):
        text = self.report()
        self.assertIn('train time:', text)
        self.assertIn('validation time:', text)
        self.assertIn('checkpoint time:', text)
        self.assertIn('epoch time:', text)
        self.assertIn('~00:20 (measured epoch average; estimate)', text)
        self.assertNotIn('~', self.report(remaining=0))

    def test_smoke_subset_is_never_described_as_full_validation(self):
        text = self.report(smoke=True)
        self.assertIn('complete-document smoke subset; not a benchmark', text)
        self.assertNotIn('full validation', text)

    def test_default_budget_does_not_change_batch_or_selection_configuration(self):
        self.assertEqual(DEFAULT_EPOCHS, 3)
        self.assertIsNone(parser().parse_args([]).epochs)
        config = TrainingConfig()
        self.assertEqual((config.batch_size, config.focus_batch_size, config.focus_every), (32, 16, 8))
        self.assertEqual(config.patience, 5)

    def test_make_default_and_continue_command_keep_resume_configuration(self):
        source = (Path(__file__).resolve().parents[3] / 'Makefile').read_text()
        self.assertIn('GO_EPOCHS ?= 3', source)
        self.assertIn('GO_BATCH_SIZE ?= 32', source)
        continuation = source.split('continue-go:', 1)[1].split('\npredict-go:', 1)[0]
        self.assertIn('--resume', continuation)
        self.assertNotIn('--batch-size', continuation)
        self.assertIn('--log-every', continuation)

    def test_short_default_run_and_resume_report_actual_budget_and_scores(self):
        threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, threads)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            snapshot = synthetic_snapshot(folder / 'snapshot')
            # An unreadable final test split remains untouched by training/reporting.
            (snapshot / 'test/input_ids.bin').write_bytes(b'held-out')
            output = folder / 'run'
            args = parser().parse_args(['--snapshot', str(snapshot), '--output-dir', str(output),
                                        '--device', 'cpu', '--cpu-threads', '1', '--batch-size', '2',
                                        '--focus-batch-size', '2', '--focus-every', '1', '--log-every', '1'])
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                run(args, model_config=ModelConfig(width=16, heads=2, layers=1, feed_forward=32))
            text = captured.getvalue()
            for header in ['Epoch 1 (run 1/3)', 'Epoch 2 (run 2/3)', 'Epoch 3 (run 3/3)']:
                self.assertIn(header, text)
            self.assertIn('Epoch budget: 3 additional epoch(s)', text)
            self.assertIn('awaiting the first complete epoch', text)
            self.assertIn('Completed 3/3 requested epoch(s); last epoch: 3.', text)
            first = load_checkpoint(output / 'last.pt')
            self.assertEqual(first['epoch'], 3)
            record = json.loads((output / 'epochs/epoch-0003.json').read_text())
            score = record['validation']['streams']['natural']['exactSpan']['f1']
            self.assertIn(f'{score:.4f}', text)
            self.assertGreaterEqual(record['timing']['epochSeconds'], record['training']['seconds'])
            self.assertEqual(record['runEpochBudget'], 3)
            self.assertIn('excludes modifiers', json.loads((output / 'run.json').read_text())['selection'])
            saved_config = first['trainingConfig'].copy()
            args = parser().parse_args(['--resume', str(output / 'last.pt'), '--epochs', '1',
                                        '--device', 'cpu', '--cpu-threads', '1'])
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                run(args)
            self.assertIn('Epoch 4 (run 1/1)', captured.getvalue())
            self.assertIn('Optimizer state: restored', captured.getvalue())
            self.assertEqual(load_checkpoint(output / 'last.pt')['trainingConfig'], saved_config)
            self.assertEqual(load_checkpoint(output / 'last.pt')['epoch'], 4)


if __name__ == '__main__':
    unittest.main()
