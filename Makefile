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
