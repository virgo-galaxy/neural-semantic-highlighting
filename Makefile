.PHONY: \
	check \
	dataset \
	dataset-typescript \
	train-typescript \
	continue-typescript \
	inspect-overlap-windows-typescript \
	train-overlap-typescript \
	continue-overlap-typescript \
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
