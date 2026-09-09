.PHONY: \
	check \
	dataset \
	dataset-typescript \
	train-typescript \
	continue-typescript \
	inspect-overlap-windows-typescript \
	train-overlap-typescript \
	continue-overlap-typescript \
	inspect-span-aware-windows-typescript \
	train-span-aware-typescript \
	continue-span-aware-typescript \
	test-windowing-golden-typescript \
	inspect-string-aware-windows-typescript \
	train-string-aware-typescript \
	continue-string-aware-typescript \
	inspect-dual-view-windows-typescript \
	train-dual-view-typescript \
	continue-dual-view-typescript \
	inspect-v3-windows-typescript \
	train-v3-typescript \
	continue-v3-typescript \
	validate-regexp-challenge-typescript \
	challenge-regexp-typescript \
	test-regexp-surgery-golden-typescript \
	surgery-regexp-typescript \
	evaluate-regexp-surgery-typescript \
	probe-regexp-surgery-typescript \
	validate-regexp-paired-challenge-typescript \
	challenge-regexp-paired-typescript \
	test-string-surgery-golden-typescript \
	surgery-string-typescript \
	evaluate-string-surgery-typescript \
	probe-string-surgery-typescript \
	evaluate-typescript \
	predict-typescript \
	benchmark-typescript \
	analyze-errors-typescript

PYTHON := .venv/bin/python

EPOCHS ?= 32
BATCH_SIZE ?= 32
PATIENCE ?= 5
TRAIN_STRIDE ?= 512
OVERLAP_TRAIN_STRIDE ?= 256
OVERLAP_OUTPUT_DIR ?= artifacts/typescript/v2-multitask-train-overlap256
SPAN_AWARE_OUTPUT_DIR ?= artifacts/typescript/v2-multitask-train-span-aware
STRING_AWARE_OUTPUT_DIR ?= artifacts/typescript/v2-multitask-train-string-aware
DUAL_VIEW_OUTPUT_DIR ?= artifacts/typescript/v2-multitask-train-dual-view50
DUAL_VIEW_EPOCHS ?= 16
DUAL_VIEW_PATIENCE ?= 16
V3_OUTPUT_DIR ?= artifacts/typescript/v3-local-role-dual-view-hard-string-regexp
V3_EPOCHS ?= 20
V3_PATIENCE ?= 20
REGEXP_CHALLENGE_CHECKPOINT ?= artifacts/typescript/v2-multitask-train-dual-view50/best-epoch20.pt
REGEXP_CHALLENGE_OUTPUT ?= artifacts/typescript/v2-multitask-train-dual-view50/regexp-challenge-epoch20.json
REGEXP_CHALLENGE_STRIDE ?= 256
REGEXP_CHALLENGE_FUSION ?= uniform
REGEXP_CHALLENGE_MAX_ERRORS ?= 40
REGEXP_SURGERY_BASE ?= artifacts/typescript/v3-local-role-dual-view-hard-string-regexp/best-epoch19.pt
REGEXP_SURGERY_DIR ?= artifacts/typescript/v3-regexp-surgery-probe
REGEXP_SURGERY_OUTPUT ?= $(REGEXP_SURGERY_DIR)/step-0400.pt
REGEXP_SURGERY_STEPS ?= 400
REGEXP_SURGERY_BATCH_SIZE ?= 16
REGEXP_SURGERY_LR ?= 5e-5
REGEXP_SURGERY_HALO ?= 16
REGEXP_SURGERY_CONTEXT_BEFORE ?= 128
REGEXP_SURGERY_REPLAY_EVERY ?= 5
REGEXP_SURGERY_SNAPSHOT_EVERY ?= 100
REGEXP_PAIRED_CHALLENGE_OUTPUT ?= artifacts/typescript/regexp-paired-context-challenge.json
REGEXP_PAIRED_CHALLENGE_STRIDE ?= 256
REGEXP_PAIRED_CHALLENGE_FUSION ?= uniform
STRING_SURGERY_BASE ?= artifacts/typescript/v3-local-role-dual-view-hard-string-regexp/best-epoch19.pt
STRING_SURGERY_DIR ?= artifacts/typescript/v3-string-surgery-probe
STRING_SURGERY_OUTPUT ?= $(STRING_SURGERY_DIR)/step-0400.pt
STRING_SURGERY_STEPS ?= 400
STRING_SURGERY_BATCH_SIZE ?= 16
STRING_SURGERY_LR ?= 5e-5
STRING_SURGERY_MIN_SPAN ?= 256
STRING_SURGERY_FIRST_INSIDE ?= 128
STRING_SURGERY_STEP_BYTES ?= 256
STRING_SURGERY_MIN_REMAINING ?= 64
STRING_SURGERY_RIGHT_HALO ?= 16
STRING_SURGERY_REPLAY_EVERY ?= 5
STRING_SURGERY_SNAPSHOT_EVERY ?= 100
SYNTH_STRING_SURGERY_BASE ?= artifacts/typescript/v3-local-role-dual-view-hard-string-regexp/best-epoch19.pt
SYNTH_STRING_SURGERY_DIR ?= artifacts/typescript/v3-string-surgery-synthetic-code-probe
SYNTH_STRING_SURGERY_OUTPUT ?= $(SYNTH_STRING_SURGERY_DIR)/step-0400.pt
SYNTH_STRING_SURGERY_STEPS ?= 400
SYNTH_STRING_SURGERY_BATCH_SIZE ?= 16
SYNTH_STRING_SURGERY_LR ?= 5e-5
SYNTH_STRING_SURGERY_TARGET_BODY ?= 768
SYNTH_STRING_SURGERY_MIN_BODY ?= 640
SYNTH_STRING_SURGERY_MAX_DOCS ?= 1200
SYNTH_STRING_SURGERY_MAX_PER_SOURCE ?= 2
SYNTH_STRING_SURGERY_SCORE_THRESHOLD ?= 18
SYNTH_STRING_SURGERY_MAX_STRING_COMMENT_RATIO ?= 0.35
SYNTH_STRING_SURGERY_FIRST_INSIDE ?= 128
SYNTH_STRING_SURGERY_STEP_BYTES ?= 256
SYNTH_STRING_SURGERY_MIN_REMAINING ?= 64
SYNTH_STRING_SURGERY_RIGHT_HALO ?= 16
SYNTH_STRING_SURGERY_REPLAY_EVERY ?= 5
SYNTH_STRING_SURGERY_SNAPSHOT_EVERY ?= 100
BENCHMARK_WINDOWS ?= 8192
BENCHMARK_WARMUP_STEPS ?= 5
BENCHMARK_BATCH_SIZES ?= 16 32 64 128
ANALYSIS_SPLIT ?= validation
ANALYSIS_EXAMPLES ?= 30
RESUME ?= artifacts/typescript/v2-multitask/last.pt

check:
	pnpm all

dataset: dataset-typescript

dataset-typescript:
	pnpm dataset:collect:typescript
	pnpm dataset:label:typescript
	pnpm dataset:validate:typescript
	pnpm dataset:split:typescript

train-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-stride $(TRAIN_STRIDE)

continue-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-stride $(TRAIN_STRIDE) \
		--resume $(RESUME)

inspect-overlap-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--train-stride $(OVERLAP_TRAIN_STRIDE)

train-overlap-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-stride $(OVERLAP_TRAIN_STRIDE) \
		--output $(OVERLAP_OUTPUT_DIR)/best.pt \
		--last-output $(OVERLAP_OUTPUT_DIR)/last.pt

continue-overlap-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-stride $(OVERLAP_TRAIN_STRIDE) \
		--output $(OVERLAP_OUTPUT_DIR)/best.pt \
		--last-output $(OVERLAP_OUTPUT_DIR)/last.pt \
		--resume $(OVERLAP_OUTPUT_DIR)/last.pt

inspect-span-aware-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--train-window-strategy span-aware \
		--train-stride 512

train-span-aware-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-window-strategy span-aware \
		--train-stride 512 \
		--output $(SPAN_AWARE_OUTPUT_DIR)/best.pt \
		--last-output $(SPAN_AWARE_OUTPUT_DIR)/last.pt

continue-span-aware-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-window-strategy span-aware \
		--train-stride 512 \
		--output $(SPAN_AWARE_OUTPUT_DIR)/best.pt \
		--last-output $(SPAN_AWARE_OUTPUT_DIR)/last.pt \
		--resume $(SPAN_AWARE_OUTPUT_DIR)/last.pt

test-windowing-golden-typescript:
	$(PYTHON) training/typescript/windowing_golden.py

inspect-string-aware-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--train-window-strategy string-aware \
		--train-stride 512

train-string-aware-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-window-strategy string-aware \
		--train-stride 512 \
		--output $(STRING_AWARE_OUTPUT_DIR)/best.pt \
		--last-output $(STRING_AWARE_OUTPUT_DIR)/last.pt

continue-string-aware-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--train-window-strategy string-aware \
		--train-stride 512 \
		--output $(STRING_AWARE_OUTPUT_DIR)/best.pt \
		--last-output $(STRING_AWARE_OUTPUT_DIR)/last.pt \
		--resume $(STRING_AWARE_OUTPUT_DIR)/last.pt

inspect-dual-view-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--train-window-strategy dual-view \
		--train-stride 512

train-dual-view-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(DUAL_VIEW_EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(DUAL_VIEW_PATIENCE) \
		--train-window-strategy dual-view \
		--train-stride 512 \
		--output $(DUAL_VIEW_OUTPUT_DIR)/best.pt \
		--last-output $(DUAL_VIEW_OUTPUT_DIR)/last.pt

continue-dual-view-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(DUAL_VIEW_EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(DUAL_VIEW_PATIENCE) \
		--train-window-strategy dual-view \
		--train-stride 512 \
		--output $(DUAL_VIEW_OUTPUT_DIR)/best.pt \
		--last-output $(DUAL_VIEW_OUTPUT_DIR)/last.pt \
		--resume $(DUAL_VIEW_OUTPUT_DIR)/last.pt

inspect-v3-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--train-window-strategy dual-view-hard-string-regexp \
		--train-stride 512

train-v3-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(V3_EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(V3_PATIENCE) \
		--train-window-strategy dual-view-hard-string-regexp \
		--train-stride 512 \
		--output $(V3_OUTPUT_DIR)/best.pt \
		--last-output $(V3_OUTPUT_DIR)/last.pt

continue-v3-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(V3_EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(V3_PATIENCE) \
		--train-window-strategy dual-view-hard-string-regexp \
		--train-stride 512 \
		--output $(V3_OUTPUT_DIR)/best.pt \
		--last-output $(V3_OUTPUT_DIR)/last.pt \
		--resume $(V3_OUTPUT_DIR)/last.pt

validate-regexp-challenge-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py \
		--validate-only

challenge-regexp-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py \
		--checkpoint $(REGEXP_CHALLENGE_CHECKPOINT) \
		--stride $(REGEXP_CHALLENGE_STRIDE) \
		--fusion $(REGEXP_CHALLENGE_FUSION) \
		--max-errors $(REGEXP_CHALLENGE_MAX_ERRORS) \
		--output $(REGEXP_CHALLENGE_OUTPUT)

test-regexp-surgery-golden-typescript:
	$(PYTHON) training/typescript/regexp_surgery_golden.py

surgery-regexp-typescript:
	$(PYTHON) training/typescript/regexp_surgery.py \
		--checkpoint $(REGEXP_SURGERY_BASE) \
		--output $(REGEXP_SURGERY_OUTPUT) \
		--steps $(REGEXP_SURGERY_STEPS) \
		--batch-size $(REGEXP_SURGERY_BATCH_SIZE) \
		--learning-rate $(REGEXP_SURGERY_LR) \
		--halo-bytes $(REGEXP_SURGERY_HALO) \
		--context-before-bytes $(REGEXP_SURGERY_CONTEXT_BEFORE) \
		--replay-every $(REGEXP_SURGERY_REPLAY_EVERY) \
		--snapshot-every $(REGEXP_SURGERY_SNAPSHOT_EVERY)

evaluate-regexp-surgery-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py \
		--checkpoint $(REGEXP_SURGERY_OUTPUT) \
		--stride 256 \
		--fusion uniform \
		--max-errors 40 \
		--output $(REGEXP_SURGERY_DIR)/regexp-challenge.json
	$(PYTHON) training/typescript/analyze_errors.py \
		--checkpoint $(REGEXP_SURGERY_OUTPUT) \
		--split validation \
		--stride 256 \
		--output $(REGEXP_SURGERY_DIR)/validation-errors.json \
		--text-output $(REGEXP_SURGERY_DIR)/validation-errors.txt \
		--max-examples 50 \
		--max-confusions 50 \
		--max-boundary-summary 50

probe-regexp-surgery-typescript: test-regexp-surgery-golden-typescript surgery-regexp-typescript evaluate-regexp-surgery-typescript

validate-regexp-paired-challenge-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py \
		--validate-only

challenge-regexp-paired-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py \
		--stride $(REGEXP_PAIRED_CHALLENGE_STRIDE) \
		--fusion $(REGEXP_PAIRED_CHALLENGE_FUSION) \
		--output $(REGEXP_PAIRED_CHALLENGE_OUTPUT)

test-string-surgery-golden-typescript:
	$(PYTHON) training/typescript/string_surgery_golden.py

surgery-string-typescript:
	$(PYTHON) training/typescript/string_surgery.py \
		--checkpoint $(STRING_SURGERY_BASE) \
		--output $(STRING_SURGERY_OUTPUT) \
		--steps $(STRING_SURGERY_STEPS) \
		--batch-size $(STRING_SURGERY_BATCH_SIZE) \
		--learning-rate $(STRING_SURGERY_LR) \
		--min-span-bytes $(STRING_SURGERY_MIN_SPAN) \
		--first-inside-offset-bytes $(STRING_SURGERY_FIRST_INSIDE) \
		--step-bytes $(STRING_SURGERY_STEP_BYTES) \
		--min-remaining-bytes $(STRING_SURGERY_MIN_REMAINING) \
		--right-halo-bytes $(STRING_SURGERY_RIGHT_HALO) \
		--replay-every $(STRING_SURGERY_REPLAY_EVERY) \
		--snapshot-every $(STRING_SURGERY_SNAPSHOT_EVERY)

evaluate-string-surgery-typescript:
	$(PYTHON) training/typescript/inspect_boundary_logits.py \
		--checkpoint $(STRING_SURGERY_OUTPUT) \
		--split validation \
		--stride 256 \
		--fusion uniform \
		--token-type string \
		--output $(STRING_SURGERY_DIR)/string-fragmentation.json \
		--max-examples 50
	$(PYTHON) training/typescript/analyze_errors.py \
		--checkpoint $(STRING_SURGERY_OUTPUT) \
		--split validation \
		--stride 256 \
		--output $(STRING_SURGERY_DIR)/validation-errors.json \
		--text-output $(STRING_SURGERY_DIR)/validation-errors.txt \
		--max-examples 50 \
		--max-confusions 50 \
		--max-boundary-summary 50

probe-string-surgery-typescript: test-string-surgery-golden-typescript surgery-string-typescript evaluate-string-surgery-typescript


test-synthetic-string-surgery-golden-typescript:
	$(PYTHON) training/typescript/synthetic_string_surgery_golden.py

surgery-synthetic-string-typescript:
	$(PYTHON) training/typescript/synthetic_string_surgery.py \
		--checkpoint $(SYNTH_STRING_SURGERY_BASE) \
		--output $(SYNTH_STRING_SURGERY_OUTPUT) \
		--steps $(SYNTH_STRING_SURGERY_STEPS) \
		--batch-size $(SYNTH_STRING_SURGERY_BATCH_SIZE) \
		--learning-rate $(SYNTH_STRING_SURGERY_LR) \
		--target-body-bytes $(SYNTH_STRING_SURGERY_TARGET_BODY) \
		--min-body-bytes $(SYNTH_STRING_SURGERY_MIN_BODY) \
		--max-synthetic-documents $(SYNTH_STRING_SURGERY_MAX_DOCS) \
		--max-per-source-document $(SYNTH_STRING_SURGERY_MAX_PER_SOURCE) \
		--score-threshold $(SYNTH_STRING_SURGERY_SCORE_THRESHOLD) \
		--max-string-comment-ratio $(SYNTH_STRING_SURGERY_MAX_STRING_COMMENT_RATIO) \
		--first-inside-offset-bytes $(SYNTH_STRING_SURGERY_FIRST_INSIDE) \
		--step-bytes $(SYNTH_STRING_SURGERY_STEP_BYTES) \
		--min-remaining-bytes $(SYNTH_STRING_SURGERY_MIN_REMAINING) \
		--right-halo-bytes $(SYNTH_STRING_SURGERY_RIGHT_HALO) \
		--replay-every $(SYNTH_STRING_SURGERY_REPLAY_EVERY) \
		--snapshot-every $(SYNTH_STRING_SURGERY_SNAPSHOT_EVERY)

evaluate-synthetic-string-surgery-typescript:
	$(PYTHON) training/typescript/inspect_boundary_logits.py \
		--checkpoint $(SYNTH_STRING_SURGERY_OUTPUT) \
		--split validation \
		--stride 256 \
		--fusion uniform \
		--token-type string \
		--output $(SYNTH_STRING_SURGERY_DIR)/string-fragmentation.json \
		--max-examples 50
	$(PYTHON) training/typescript/analyze_errors.py \
		--checkpoint $(SYNTH_STRING_SURGERY_OUTPUT) \
		--split validation \
		--stride 256 \
		--output $(SYNTH_STRING_SURGERY_DIR)/validation-errors.json \
		--text-output $(SYNTH_STRING_SURGERY_DIR)/validation-errors.txt \
		--max-examples 50 \
		--max-confusions 50 \
		--max-boundary-summary 50

probe-synthetic-string-surgery-typescript: test-synthetic-string-surgery-golden-typescript surgery-synthetic-string-typescript evaluate-synthetic-string-surgery-typescript

evaluate-typescript:
	$(PYTHON) training/typescript/evaluate.py

predict-typescript:
	$(PYTHON) training/typescript/predict.py

benchmark-typescript:
	$(PYTHON) training/typescript/benchmark.py \
		--windows $(BENCHMARK_WINDOWS) \
		--warmup-steps $(BENCHMARK_WARMUP_STEPS) \
		--batch-sizes $(BENCHMARK_BATCH_SIZES)

analyze-errors-typescript:
	$(PYTHON) training/typescript/analyze_errors.py \
		--split $(ANALYSIS_SPLIT) \
		--max-examples $(ANALYSIS_EXAMPLES)
