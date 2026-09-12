.PHONY: \
	check \
	test-labeling-go \
	dataset \
	dataset-typescript \
	dataset-go \
	dataset-go-official \
	dataset-go-applications \
	dataset-go-focused \
	dataset-go-focused-v2 \
	dataset-go-v3 \
	dataset-go-v3-curriculum \
	dataset-go-v3-real \
	dataset-go-targeted \
	dataset-go-sealed \
	dataset-go-prepare \
	test-training-data-go \
	train-go-smoke \
	train-go \
	train-go-v2 \
	train-go-v3-check \
	train-go-final \
	continue-go \
	predict-go \
	evaluate-go \
	evaluate-go-sealed \
	dataset-go-collect \
	dataset-go-label \
	dataset-go-validate \
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
GO_GOLD_TOOLCHAIN := go1.27.1
GO_CORPUS ?=
GO_DEVICE ?= auto
GO_EPOCHS ?= 3
GO_BATCH_SIZE ?= 32
GO_FOCUS_BATCH_SIZE ?= 16
GO_FOCUS_EVERY ?= 8
GO_FOCUS_SAMPLING ?= feature-balanced
GO_FOCUS_FEATURES ?=
GO_FOCUS_V2_VARIANTS ?= 8
GO_FOCUS_V3_VARIANTS ?= 8
GO_V3_FOCUS_EVERY ?= 4
GO_FINAL_EPOCHS ?= 40
GO_SEALED_VARIANTS ?= 16
GO_INIT_CHECKPOINT ?=
GO_LOG_EVERY ?= 25
GO_RUN ?=
GO_CHECKPOINT ?=
GO_SOURCE ?=
GO_EVAL_SPLIT ?= validation

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
	$(MAKE) test-labeling-go
	$(MAKE) test-training-data-go
	$(PYTHON) -m compileall -q training/typescript packs/typescript/runtime
	$(PYTHON) -c 'import importlib, pathlib, sys; sys.path.insert(0, "training/typescript"); [importlib.import_module(path.stem) for path in pathlib.Path("training/typescript").glob("*.py")]'
	$(PYTHON) -c 'import packs.typescript.runtime.local'


test-labeling-go:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go test ./...

dataset: dataset-typescript

dataset-typescript:
	pnpm dataset:collect:typescript
	pnpm dataset:label:typescript
	pnpm dataset:validate:typescript
	pnpm dataset:split:typescript

dataset-go:
	$(MAKE) dataset-go-collect
	$(MAKE) dataset-go-label
	$(MAKE) dataset-go-validate

dataset-go-official:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules --config dataset/sources/official.json --source "$(GO_CORPUS)"

dataset-go-applications:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules --config dataset/sources/applications.json --source "$(GO_CORPUS)"

dataset-go-focused:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-focus

dataset-go-focused-v2:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-focus \
		--profile v2r3 --id modern-v2r3 --variants $(GO_FOCUS_V2_VARIANTS)

# V3 is the clean integrated curriculum candidate. Historical V2 corpora remain
# immutable for experiment replay but are not selected by training/go/corpora.json.
dataset-go-v3-curriculum:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-focus \
		--profile v3 --id modern-v3 --variants $(GO_FOCUS_V3_VARIANTS)

dataset-go-v3-real:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules \
		--config dataset/sources/targeted.json --source "$(GO_CORPUS)"
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-mine \
		--config dataset/sources/targeted.json --id real-world-v3

dataset-go-v3: dataset-go-v3-real dataset-go-v3-curriculum dataset-go-prepare

dataset-go-targeted:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules \
		--config dataset/sources/targeted.json --source "$(GO_CORPUS)"
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-mine \
		--config dataset/sources/targeted.json --id targeted-real-v2r1

dataset-go-sealed:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules \
		--config dataset/sources/sealed.json --source "$(GO_CORPUS)"
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-focus \
		--profile sealed-v1 --id sealed-modern-v1 --variants $(GO_SEALED_VARIANTS)

dataset-go-prepare:
	$(PYTHON) training/go/prepare.py

test-training-data-go:
	$(PYTHON) -m unittest discover -s training/go/tests -v

dataset-go-collect:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset collect

dataset-go-label:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset label

dataset-go-validate:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset validate

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

# Go training reads prepared snapshots; it never recollects or relabels corpora.
train-go-smoke:
	$(PYTHON) training/go/train.py --smoke --epochs 1 --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling $(GO_FOCUS_SAMPLING) $(if $(GO_FOCUS_FEATURES),--focus-features "$(GO_FOCUS_FEATURES)") --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

train-go:
	$(PYTHON) training/go/train.py --epochs $(GO_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling $(GO_FOCUS_SAMPLING) $(if $(GO_FOCUS_FEATURES),--focus-features "$(GO_FOCUS_FEATURES)") --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

train-go-v2:
	@test -n "$(GO_INIT_CHECKPOINT)" || (echo 'Set GO_INIT_CHECKPOINT to the V1 Go best.pt'; exit 1)
	$(PYTHON) training/go/train.py --init-from "$(GO_INIT_CHECKPOINT)" --epochs $(GO_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling $(GO_FOCUS_SAMPLING) $(if $(GO_FOCUS_FEATURES),--focus-features "$(GO_FOCUS_FEATURES)") --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

# Short V3 verification: transfer only weights from the strongest diagnostic
# checkpoint, then validate the frozen candidate curriculum and quality gates.
train-go-v3-check:
	@test -n "$(GO_INIT_CHECKPOINT)" || (echo 'Set GO_INIT_CHECKPOINT to the current strongest Go best.pt'; exit 1)
	@test -z "$(GO_FOCUS_FEATURES)" || (echo 'V3 verification uses the full curriculum; unset GO_FOCUS_FEATURES'; exit 1)
	$(PYTHON) training/go/train.py --init-from "$(GO_INIT_CHECKPOINT)" --epochs $(GO_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_V3_FOCUS_EVERY) --focus-sampling feature-balanced \
		--selection-policy quality-gated --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

# Final training is intentionally unable to inherit a previous checkpoint or a
# feature-specific patch schedule. It starts from random initialization.
train-go-final:
	@test -z "$(GO_INIT_CHECKPOINT)" || (echo 'Final training must start from random initialization; unset GO_INIT_CHECKPOINT'; exit 1)
	@test -z "$(GO_FOCUS_FEATURES)" || (echo 'Final training uses the complete V3 curriculum; unset GO_FOCUS_FEATURES'; exit 1)
	$(PYTHON) training/go/train.py --epochs $(GO_FINAL_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_V3_FOCUS_EVERY) --focus-sampling feature-balanced \
		--selection-policy quality-gated --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

continue-go:
	@test -n "$(GO_CHECKPOINT)" || (echo 'Set GO_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) training/go/train.py --resume "$(GO_CHECKPOINT)" --epochs $(GO_EPOCHS) --device $(GO_DEVICE) --log-every $(GO_LOG_EVERY)

predict-go:
	@test -n "$(GO_CHECKPOINT)" || (echo 'Set GO_CHECKPOINT to a Go checkpoint'; exit 1)
	$(PYTHON) training/go/predict.py --checkpoint "$(GO_CHECKPOINT)" --device $(GO_DEVICE) \
		$(if $(GO_SOURCE),--source "$(GO_SOURCE)")

evaluate-go:
	@test -n "$(GO_CHECKPOINT)" || (echo 'Set GO_CHECKPOINT to a Go checkpoint'; exit 1)
	$(PYTHON) training/go/evaluate.py --checkpoint "$(GO_CHECKPOINT)" --device $(GO_DEVICE) \
		--split $(GO_EVAL_SPLIT) --inference adaptive

# One-time external acceptance. dataset-go-sealed creates only external corpora;
# they are rejected by training/go/prepare.py and cannot enter a training snapshot.
evaluate-go-sealed:
	@test -n "$(GO_CHECKPOINT)" || (echo 'Set GO_CHECKPOINT to the final Go candidate checkpoint'; exit 1)
	$(PYTHON) training/go/sealed_eval.py --checkpoint "$(GO_CHECKPOINT)" --device $(GO_DEVICE)
