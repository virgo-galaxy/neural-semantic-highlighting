.PHONY: \
	check \
	dataset \
	dataset-typescript \
	train-typescript \
	continue-typescript \
	evaluate-typescript \
	predict-typescript \
	benchmark-typescript

PYTHON := .venv/bin/python

EPOCHS ?= 8
BATCH_SIZE ?= 16
PATIENCE ?= 3
BENCHMARK_WINDOWS ?= 8192
BENCHMARK_WARMUP_STEPS ?= 5
BENCHMARK_BATCH_SIZES ?= 16 32 64 128
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
		--patience $(PATIENCE)

continue-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(EPOCHS) \
		--batch-size $(BATCH_SIZE) \
		--patience $(PATIENCE) \
		--resume $(RESUME)

evaluate-typescript:
	$(PYTHON) training/typescript/evaluate.py

predict-typescript:
	$(PYTHON) training/typescript/predict.py

benchmark-typescript:
	$(PYTHON) training/typescript/benchmark.py \
		--windows $(BENCHMARK_WINDOWS) \
		--warmup-steps $(BENCHMARK_WARMUP_STEPS) \
		--batch-sizes $(BENCHMARK_BATCH_SIZES)
