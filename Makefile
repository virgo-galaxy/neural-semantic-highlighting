.PHONY: \
	check \
	dataset-html \
	dataset-html-sources \
	dataset-html-curriculum \
	dataset-html-collect \
	dataset-html-label \
	dataset-html-validate \
	dataset-html-prepare \
	test-training-data-html \
	train-html-smoke \
	train-html \
	continue-html \
	predict-html \
	evaluate-html \
	evaluate-html-composed \
	challenge-html \
	export-html-model \
	dataset-css \
	dataset-css-sources \
	dataset-css-collect \
	dataset-css-label \
	dataset-css-validate \
	dataset-css-prepare \
	test-training-data-css \
	train-css-smoke \
	train-css \
	continue-css \
	predict-css \
	evaluate-css \
	challenge-css \
	export-css-model \
	test-labeling-go \
	dataset-typescript \
	dataset-go \
	dataset-go-official \
	dataset-go-applications \
	dataset-go-focused \
	dataset-go-curriculum \
	dataset-go-targeted \
	dataset-go-prepare \
	test-training-data-go \
	train-go-smoke \
	train-go \
	train-go-final \
	continue-go \
	predict-go \
	evaluate-go \
	export-go-model \
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

VUE_DEVICE ?= auto
VUE_EPOCHS ?= 3
VUE_BATCH_SIZE ?= 32
VUE_RUN ?=
VUE_CHECKPOINT ?=
VUE_INIT_FROM ?=
VUE_SOURCE ?=
VUE_EVAL_SPLIT ?= validation
VUE_TEST_REPORT ?=

PYTHON := .venv/bin/python
HTML_DEVICE ?= auto
HTML_EPOCHS ?= 3
HTML_BATCH_SIZE ?= 32
HTML_RUN ?=
HTML_CHECKPOINT ?=
HTML_INIT_FROM ?=
HTML_SOURCE ?=
HTML_EVAL_SPLIT ?= validation
HTML_TEST_REPORT ?=
CSS_DEVICE ?= auto
CSS_EPOCHS ?= 3
CSS_BATCH_SIZE ?= 32
CSS_RUN ?=
CSS_CHECKPOINT ?=
CSS_SOURCE ?=
CSS_DOCUMENT_KIND ?= css
CSS_EVAL_SPLIT ?= validation
CSS_INIT_FROM_GO ?=
CSS_TEST_REPORT ?=
GO_GOLD_TOOLCHAIN := go1.27.1
GO_CORPUS ?=
GO_DEVICE ?= auto
GO_EPOCHS ?= 3
GO_BATCH_SIZE ?= 32
GO_FOCUS_BATCH_SIZE ?= 16
GO_FOCUS_EVERY ?= 8
GO_FOCUS_VARIANTS ?= 16
GO_FOCUS_SAMPLING ?= feature-balanced
GO_FOCUS_FEATURES ?=
GO_FINAL_EPOCHS ?= 40
GO_LOG_EVERY ?= 25
GO_RUN ?=
GO_CHECKPOINT ?=
GO_SOURCE ?=
GO_EVAL_SPLIT ?= validation
GO_TEST_REPORT ?=

TYPESCRIPT_MAX_LENGTH ?= 512
TYPESCRIPT_EPOCHS ?= 32
TYPESCRIPT_BATCH_SIZE ?= 32
TYPESCRIPT_PATIENCE ?= 5
TYPESCRIPT_ARTIFACT_DIR ?= artifacts/typescript/run
TYPESCRIPT_RESUME ?= $(TYPESCRIPT_ARTIFACT_DIR)/last.pt
TYPESCRIPT_BENCHMARK_WINDOWS ?= 64
TYPESCRIPT_BENCHMARK_WARMUP_STEPS ?= 2
TYPESCRIPT_BENCHMARK_BATCH_SIZES ?= 1 2 4 8
TYPESCRIPT_ANALYSIS_SPLIT ?= validation
TYPESCRIPT_ANALYSIS_EXAMPLES ?= 30

check:
	pnpm all
	$(MAKE) test-labeling-go
	$(MAKE) test-training-data-go
	$(MAKE) test-training-data-css
	$(MAKE) test-training-data-html
	$(MAKE) test-training-data-vue
	$(MAKE) test-training-data-shared
	$(PYTHON) -m unittest discover -s packs/python/tests -v
	$(PYTHON) -m compileall -q training/shared training/python packs/python/runtime
	$(PYTHON) -c 'import packs.python.runtime.local'
	$(MAKE) test-labeling-bash
	$(PYTHON) -m compileall -q training/bash packs/bash/runtime
	$(PYTHON) -c 'import packs.bash.runtime.local'
	$(MAKE) test-labeling-perl
	$(PYTHON) -m compileall -q training/perl packs/perl/runtime
	$(PYTHON) -c 'import packs.perl.runtime.local'
	$(MAKE) test-labeling-awk
	$(PYTHON) -m compileall -q training/awk packs/awk/runtime
	$(PYTHON) -c 'import packs.awk.runtime.local'
	$(MAKE) test-labeling-sql
	$(MAKE) test-labeling-powershell
	$(PYTHON) -m compileall -q training/sql packs/sql/runtime
	$(PYTHON) -m compileall -q training/powershell packs/powershell/runtime
	$(PYTHON) -c 'import packs.sql.runtime.local'
	$(PYTHON) -c 'import packs.powershell.runtime.local'
	$(PYTHON) -m compileall -q training/typescript packs/typescript/runtime training/go packs/go/runtime training/css
	$(PYTHON) -c 'import importlib, pathlib, sys; sys.path.insert(0, "training/typescript"); [importlib.import_module(path.stem) for path in pathlib.Path("training/typescript").glob("*.py")]'
	$(PYTHON) -c 'import packs.typescript.runtime.local'
	$(PYTHON) -c 'import packs.go.runtime.local'
	$(PYTHON) -c 'import packs.css.runtime.local'
	$(PYTHON) -m compileall -q training/html packs/html/runtime
	$(PYTHON) -c 'import packs.html.runtime.local'
	$(PYTHON) -m compileall -q training/vue packs/vue/runtime
	$(PYTHON) -c 'import packs.vue.runtime.local'

include training/shared/Makefile

dataset-html-sources:
	$(PYTHON) packs/html/dataset/fetch_sources.py

dataset-html-curriculum:
	$(PYTHON) packs/html/dataset/generate_curriculum.py

dataset-html:
	$(MAKE) dataset-html-curriculum
	$(MAKE) dataset-html-collect
	$(MAKE) dataset-html-label
	$(MAKE) dataset-html-validate
	$(MAKE) dataset-html-prepare

dataset-html-collect:
	pnpm dataset:collect:html

dataset-html-label:
	pnpm dataset:label:html

dataset-html-validate:
	pnpm dataset:validate:html

dataset-html-prepare:
	$(PYTHON) -m training.html.prepare

test-training-data-html:
	$(PYTHON) -m unittest discover -s training/html/tests -v

train-html-smoke:
	$(PYTHON) -m training.html.train --smoke --epochs 1 --device $(HTML_DEVICE) \
		--batch-size $(HTML_BATCH_SIZE) $(if $(HTML_RUN),--output-dir "$(HTML_RUN)")

train-html:
	$(PYTHON) -m training.html.train --epochs $(HTML_EPOCHS) --device $(HTML_DEVICE) \
		--batch-size $(HTML_BATCH_SIZE) $(if $(HTML_RUN),--output-dir "$(HTML_RUN)") \
		$(if $(HTML_INIT_FROM),--init-from "$(HTML_INIT_FROM)")

continue-html:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.html.train --resume "$(HTML_CHECKPOINT)" --epochs $(HTML_EPOCHS) --device $(HTML_DEVICE)

predict-html:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to an HTML checkpoint'; exit 1)
	@test -n "$(HTML_SOURCE)" || (echo 'Set HTML_SOURCE to an HTML source file'; exit 1)
	$(PYTHON) -m training.html.predict --checkpoint "$(HTML_CHECKPOINT)" --device $(HTML_DEVICE) --file "$(HTML_SOURCE)"

evaluate-html:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to an HTML checkpoint'; exit 1)
	$(PYTHON) -m training.html.evaluate --checkpoint "$(HTML_CHECKPOINT)" --device $(HTML_DEVICE) --split $(HTML_EVAL_SPLIT)

evaluate-html-composed:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to an HTML checkpoint'; exit 1)
	node --import tsx training/html/evaluate-composed.ts --checkpoint "$(HTML_CHECKPOINT)" --device $(HTML_DEVICE) --split $(HTML_EVAL_SPLIT)

challenge-html:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to an HTML checkpoint'; exit 1)
	$(PYTHON) -m training.html.challenge --checkpoint "$(HTML_CHECKPOINT)" --device $(HTML_DEVICE)

export-html-model:
	@test -n "$(HTML_CHECKPOINT)" || (echo 'Set HTML_CHECKPOINT to the reviewed best.pt'; exit 1)
	@test -n "$(HTML_TEST_REPORT)" || (echo 'Set HTML_TEST_REPORT to its held-out adaptive test report'; exit 1)
	$(PYTHON) -m training.html.export_model --checkpoint "$(HTML_CHECKPOINT)" --test-report "$(HTML_TEST_REPORT)"


test-labeling-go:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go test ./...


dataset-typescript:
	pnpm dataset:collect:typescript
	pnpm dataset:label:typescript
	pnpm dataset:validate:typescript
	pnpm dataset:split:typescript

dataset-css:
	$(MAKE) dataset-css-collect
	$(MAKE) dataset-css-label
	$(MAKE) dataset-css-validate
	$(MAKE) dataset-css-prepare

dataset-css-sources:
	$(PYTHON) packs/css/dataset/fetch_sources.py

dataset-css-collect:
	pnpm dataset:collect:css

dataset-css-label:
	pnpm dataset:label:css

dataset-css-validate:
	pnpm dataset:validate:css

dataset-css-prepare:
	$(PYTHON) -m training.css.prepare

test-training-data-css:
	$(PYTHON) -m unittest discover -s training/css/tests -v

train-css-smoke:
	$(PYTHON) -m training.css.train --smoke --epochs 1 --device $(CSS_DEVICE) \
		--batch-size $(CSS_BATCH_SIZE) $(if $(CSS_RUN),--output-dir "$(CSS_RUN)")

train-css:
	$(PYTHON) -m training.css.train --epochs $(CSS_EPOCHS) --device $(CSS_DEVICE) \
		--batch-size $(CSS_BATCH_SIZE) $(if $(CSS_RUN),--output-dir "$(CSS_RUN)") \
		$(if $(CSS_INIT_FROM_GO),--init-from-go "$(CSS_INIT_FROM_GO)")

continue-css:
	@test -n "$(CSS_CHECKPOINT)" || (echo 'Set CSS_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.css.train --resume "$(CSS_CHECKPOINT)" --epochs $(CSS_EPOCHS) --device $(CSS_DEVICE)

predict-css:
	@test -n "$(CSS_CHECKPOINT)" || (echo 'Set CSS_CHECKPOINT to a CSS checkpoint'; exit 1)
	@test -n "$(CSS_SOURCE)" || (echo 'Set CSS_SOURCE to a CSS/SCSS/Less source file'; exit 1)
	$(PYTHON) -m training.css.predict --checkpoint "$(CSS_CHECKPOINT)" --device $(CSS_DEVICE) \
		--file "$(CSS_SOURCE)" --document-kind $(CSS_DOCUMENT_KIND)

evaluate-css:
	@test -n "$(CSS_CHECKPOINT)" || (echo 'Set CSS_CHECKPOINT to a CSS checkpoint'; exit 1)
	$(PYTHON) -m training.css.evaluate --checkpoint "$(CSS_CHECKPOINT)" --device $(CSS_DEVICE) \
		--split $(CSS_EVAL_SPLIT) --inference adaptive

challenge-css:
	@test -n "$(CSS_CHECKPOINT)" || (echo 'Set CSS_CHECKPOINT to a CSS checkpoint'; exit 1)
	$(PYTHON) -m training.css.challenge --checkpoint "$(CSS_CHECKPOINT)" --device $(CSS_DEVICE)

export-css-model:
	@test -n "$(CSS_CHECKPOINT)" || (echo 'Set CSS_CHECKPOINT to the reviewed best.pt'; exit 1)
	@test -n "$(CSS_TEST_REPORT)" || (echo 'Set CSS_TEST_REPORT to its held-out adaptive test report'; exit 1)
	$(PYTHON) -m training.css.export_model --checkpoint "$(CSS_CHECKPOINT)" --test-report "$(CSS_TEST_REPORT)"

dataset-go:
	$(MAKE) dataset-go-collect
	$(MAKE) dataset-go-label
	$(MAKE) dataset-go-validate

dataset-go-official:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules --config dataset/sources/official.json --source "$(GO_CORPUS)"

dataset-go-applications:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules --config dataset/sources/applications.json --source "$(GO_CORPUS)"

dataset-go-focused:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-focus \
		--id modern --variants $(GO_FOCUS_VARIANTS)

dataset-go-targeted:
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-dataset modules \
		--config dataset/sources/targeted.json --source "$(GO_CORPUS)"
	cd packs/go && GOTOOLCHAIN=$(GO_GOLD_TOOLCHAIN) go run ./dataset/cmd/nsh-go-mine \
		--config dataset/sources/targeted.json --id targeted-real

# Build the complete version-neutral focused curriculum, then publish a new
# immutable prepared snapshot. Existing natural corpora are reused.
dataset-go-curriculum:
	$(MAKE) dataset-go-targeted
	$(MAKE) dataset-go-focused
	$(MAKE) dataset-go-prepare

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
		--max-length $(TYPESCRIPT_MAX_LENGTH)

test-windowing-golden-typescript:
	$(PYTHON) training/typescript/windowing_golden.py

train-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(TYPESCRIPT_EPOCHS) \
		--batch-size $(TYPESCRIPT_BATCH_SIZE) \
		--patience $(TYPESCRIPT_PATIENCE) \
		--max-length $(TYPESCRIPT_MAX_LENGTH) \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--last-output $(TYPESCRIPT_ARTIFACT_DIR)/last.pt

continue-typescript:
	$(PYTHON) training/typescript/train.py \
		--epochs $(TYPESCRIPT_EPOCHS) \
		--batch-size $(TYPESCRIPT_BATCH_SIZE) \
		--patience $(TYPESCRIPT_PATIENCE) \
		--max-length $(TYPESCRIPT_MAX_LENGTH) \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--last-output $(TYPESCRIPT_ARTIFACT_DIR)/last.pt \
		--resume $(TYPESCRIPT_RESUME)

evaluate-typescript:
	$(PYTHON) training/typescript/evaluate.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/test-metrics.json

predict-typescript:
	$(PYTHON) training/typescript/predict.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt

benchmark-typescript:
	$(PYTHON) training/typescript/benchmark.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--windows $(TYPESCRIPT_BENCHMARK_WINDOWS) \
		--warmup-steps $(TYPESCRIPT_BENCHMARK_WARMUP_STEPS) \
		--batch-sizes $(TYPESCRIPT_BENCHMARK_BATCH_SIZES)

analyze-errors-typescript:
	$(PYTHON) training/typescript/analyze_errors.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--split $(TYPESCRIPT_ANALYSIS_SPLIT) \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/error-analysis.json \
		--text-output $(TYPESCRIPT_ARTIFACT_DIR)/error-analysis.txt \
		--max-examples $(TYPESCRIPT_ANALYSIS_EXAMPLES)

inspect-fragmentation-typescript:
	$(PYTHON) training/typescript/fragmentation.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--split $(TYPESCRIPT_ANALYSIS_SPLIT) \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/fragmentation.json \
		--max-examples $(TYPESCRIPT_ANALYSIS_EXAMPLES)

validate-regexp-challenge-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py --validate-only

challenge-regexp-typescript:
	$(PYTHON) training/typescript/regexp_challenge.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--max-errors 40 \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/regexp-challenge.json

validate-regexp-paired-challenge-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py --validate-only

challenge-regexp-paired-typescript:
	$(PYTHON) training/typescript/regexp_paired_challenge.py \
		--checkpoint current=$(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/regexp-paired-context-challenge.json

validate-jsx-tsx-challenge-typescript:
	$(PYTHON) training/typescript/jsx_tsx_challenge.py --validate-only

challenge-jsx-tsx-typescript:
	$(PYTHON) training/typescript/jsx_tsx_challenge.py \
		--checkpoint $(TYPESCRIPT_ARTIFACT_DIR)/best.pt \
		--max-errors 50 \
		--output $(TYPESCRIPT_ARTIFACT_DIR)/jsx-tsx-challenge.json

# Go training reads prepared snapshots; it never recollects or relabels corpora.
train-go-smoke:
	$(PYTHON) training/go/train.py --smoke --epochs 1 --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling $(GO_FOCUS_SAMPLING) $(if $(GO_FOCUS_FEATURES),--focus-features "$(GO_FOCUS_FEATURES)") --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

train-go:
	$(PYTHON) training/go/train.py --epochs $(GO_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling $(GO_FOCUS_SAMPLING) $(if $(GO_FOCUS_FEATURES),--focus-features "$(GO_FOCUS_FEATURES)") --log-every $(GO_LOG_EVERY) $(if $(GO_RUN),--output-dir "$(GO_RUN)")

# Final training is intentionally unable to inherit a previous checkpoint or a
# feature-specific patch schedule. It starts from random initialization.
train-go-final:
	@test -z "$(GO_FOCUS_FEATURES)" || (echo 'Final training uses the complete canonical curriculum; unset GO_FOCUS_FEATURES'; exit 1)
	$(PYTHON) training/go/train.py --epochs $(GO_FINAL_EPOCHS) --device $(GO_DEVICE) \
		--batch-size $(GO_BATCH_SIZE) --focus-batch-size $(GO_FOCUS_BATCH_SIZE) \
		--focus-every $(GO_FOCUS_EVERY) --focus-sampling confusion-aware \
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

export-go-model:
	@test -n "$(GO_CHECKPOINT)" || (echo 'Set GO_CHECKPOINT to the selected Go best.pt'; exit 1)
	$(PYTHON) training/go/export_model.py --checkpoint "$(GO_CHECKPOINT)" \
		--output packs/go/model/model.pt --metadata packs/go/model/model.json \
		$(if $(GO_TEST_REPORT),--test-report "$(GO_TEST_REPORT)")


.PHONY: dataset-vue-sources dataset-vue-curriculum dataset-vue dataset-vue-collect dataset-vue-label dataset-vue-validate dataset-vue-prepare test-training-data-vue train-vue-smoke train-vue continue-vue predict-vue evaluate-vue evaluate-vue-composed challenge-vue export-vue-model

dataset-vue-sources:
	$(PYTHON) packs/vue/dataset/fetch_sources.py

dataset-vue-curriculum:
	$(PYTHON) packs/vue/dataset/generate_curriculum.py

dataset-vue:
	$(MAKE) dataset-vue-curriculum
	$(MAKE) dataset-vue-collect
	$(MAKE) dataset-vue-label
	$(MAKE) dataset-vue-validate
	$(MAKE) dataset-vue-prepare

dataset-vue-collect:
	pnpm dataset:collect:vue

dataset-vue-label:
	pnpm dataset:label:vue

dataset-vue-validate:
	pnpm dataset:validate:vue

dataset-vue-prepare:
	$(PYTHON) -m training.vue.prepare

test-training-data-vue:
	$(PYTHON) -m unittest discover -s training/vue/tests -v

train-vue-smoke:
	$(PYTHON) -m training.vue.train --smoke --epochs 1 --device $(VUE_DEVICE) \
		--batch-size $(VUE_BATCH_SIZE) $(if $(VUE_RUN),--output-dir "$(VUE_RUN)")

train-vue:
	$(PYTHON) -m training.vue.train --epochs $(VUE_EPOCHS) --device $(VUE_DEVICE) \
		--batch-size $(VUE_BATCH_SIZE) $(if $(VUE_RUN),--output-dir "$(VUE_RUN)") \
		$(if $(VUE_INIT_FROM),--init-from "$(VUE_INIT_FROM)")

continue-vue:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.vue.train --resume "$(VUE_CHECKPOINT)" --epochs $(VUE_EPOCHS) --device $(VUE_DEVICE)

predict-vue:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to an VUE checkpoint'; exit 1)
	@test -n "$(VUE_SOURCE)" || (echo 'Set VUE_SOURCE to an VUE source file'; exit 1)
	$(PYTHON) -m training.vue.predict --checkpoint "$(VUE_CHECKPOINT)" --device $(VUE_DEVICE) --file "$(VUE_SOURCE)"

evaluate-vue:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to an VUE checkpoint'; exit 1)
	$(PYTHON) -m training.vue.evaluate --checkpoint "$(VUE_CHECKPOINT)" --device $(VUE_DEVICE) --split $(VUE_EVAL_SPLIT)

evaluate-vue-composed:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to an VUE checkpoint'; exit 1)
	node --import tsx training/vue/evaluate-composed.ts --checkpoint "$(VUE_CHECKPOINT)" --device $(VUE_DEVICE) --split $(VUE_EVAL_SPLIT)

challenge-vue:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to an VUE checkpoint'; exit 1)
	$(PYTHON) -m training.vue.challenge --checkpoint "$(VUE_CHECKPOINT)" --device $(VUE_DEVICE)

export-vue-model:
	@test -n "$(VUE_CHECKPOINT)" || (echo 'Set VUE_CHECKPOINT to the reviewed best.pt'; exit 1)
	@test -n "$(VUE_TEST_REPORT)" || (echo 'Set VUE_TEST_REPORT to its held-out adaptive test report'; exit 1)
	$(PYTHON) -m training.vue.export_model --checkpoint "$(VUE_CHECKPOINT)" --test-report "$(VUE_TEST_REPORT)"
