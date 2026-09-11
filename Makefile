.PHONY: \
	check \
	dataset \
	dataset-typescript \
	inspect-windows-typescript \
	test-windowing-golden-typescript \
	train-typescript \
	continue-typescript \
	evaluate-typescript \
	predict-typescript \
	benchmark-typescript \
	analyze-errors-typescript \
	inspect-fragmentation-typescript \
	validate-regexp-challenge-typescript \
	challenge-regexp-typescript \
	validate-regexp-paired-challenge-typescript \
	challenge-regexp-paired-typescript \
	validate-jsx-tsx-challenge-typescript \
	challenge-jsx-tsx-typescript

PYTHON := .venv/bin/python

MAX_LENGTH ?= 512
EPOCHS ?= 32
BATCH_SIZE ?= 32
PATIENCE ?= 5
ARTIFACT_DIR ?= artifacts/typescript/context512-re
RESUME ?= $(ARTIFACT_DIR)/last.pt

BENCHMARK_WINDOWS ?= 64
BENCHMARK_WARMUP_STEPS ?= 2
BENCHMARK_BATCH_SIZES ?= 1 2 4 8
ANALYSIS_SPLIT ?= validation
ANALYSIS_EXAMPLES ?= 30

check:
	pnpm all
	$(PYTHON) -m compileall -q training/typescript packs/typescript/runtime
	$(PYTHON) -c 'import importlib, pathlib, sys; sys.path.insert(0, "training/typescript"); [importlib.import_module(path.stem) for path in pathlib.Path("training/typescript").glob("*.py")]'
	$(PYTHON) -c 'import packs.typescript.runtime.local'

dataset: dataset-typescript

dataset-typescript:
	pnpm dataset:collect:typescript
	pnpm dataset:label:typescript
	pnpm dataset:validate:typescript
	pnpm dataset:split:typescript

inspect-windows-typescript:
	$(PYTHON) training/typescript/dataset.py \
		--max-length $(MAX_LENGTH)

test-windowing-golden-typescript:
	$(PYTHON) training/typescript/windowing_golden.py

train-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--max-length $(MAX_LENGTH) \
		--output $(ARTIFACT_DIR)/best.pt \
		--last-output $(ARTIFACT_DIR)/last.pt

continue-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--max-length $(MAX_LENGTH) \
		--output $(ARTIFACT_DIR)/best.pt \
		--last-output $(ARTIFACT_DIR)/last.pt \
		--resume $(RESUME)

evaluate-typescript:
	$(PYTHON) training/typescript/evaluate.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--output $(ARTIFACT_DIR)/test-metrics.json

predict-typescript:
	$(PYTHON) training/typescript/predict.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt

benchmark-typescript:
	$(PYTHON) training/typescript/benchmark.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--windows $(BENCHMARK_WINDOWS) \
		--warmup-steps $(BENCHMARK_WARMUP_STEPS) \
		--batch-sizes $(BENCHMARK_BATCH_SIZES)

analyze-errors-typescript:
	$(PYTHON) training/typescript/analyze_errors.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--split $(ANALYSIS_SPLIT) \
		--output $(ARTIFACT_DIR)/error-analysis.json \
		--text-output $(ARTIFACT_DIR)/error-analysis.txt \
		--max-examples $(ANALYSIS_EXAMPLES)

inspect-fragmentation-typescript:
	$(PYTHON) training/typescript/fragmentation.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--split $(ANALYSIS_SPLIT) \
		--output $(ARTIFACT_DIR)/fragmentation.json \
		--max-examples $(ANALYSIS_EXAMPLES)

validate-regexp-challenge-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py --validate-only

challenge-regexp-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--max-errors 40 \
		--output $(ARTIFACT_DIR)/regexp-challenge.json

validate-regexp-paired-challenge-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py --validate-only

challenge-regexp-paired-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py \
		--checkpoint current=$(ARTIFACT_DIR)/best.pt \
		--output $(ARTIFACT_DIR)/regexp-paired-context-challenge.json

validate-jsx-tsx-challenge-typescript:
	$(PYTHON) training/typescript/jsx_tsx_challenge.py --validate-only

challenge-jsx-tsx-typescript:
	$(PYTHON) training/typescript/jsx_tsx_challenge.py \
		--checkpoint $(ARTIFACT_DIR)/best.pt \
		--max-errors 50 \
		--output $(ARTIFACT_DIR)/jsx-tsx-challenge.json
