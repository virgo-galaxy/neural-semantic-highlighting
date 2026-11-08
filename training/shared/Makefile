# New standalone packs preserve the existing per-pack command convention.
PYTHON_GOLD ?= artifacts/tools/python/cpython-3.15.0-macos-aarch64-none/bin/python3.15
PYTHON_DEVICE ?= auto
PYTHON_EPOCHS ?= 3
PYTHON_BATCH_SIZE ?= 32
PYTHON_EVAL_SPLIT ?= validation

.PHONY: dataset-python dataset-python-curriculum dataset-python-collect dataset-python-label dataset-python-validate dataset-python-prepare test-labeling-python test-training-data-shared train-python-smoke train-python continue-python predict-python evaluate-python challenge-python export-python-model

dataset-python:
	$(MAKE) dataset-python-curriculum
	$(MAKE) dataset-python-collect
	$(MAKE) dataset-python-label
	$(MAKE) dataset-python-validate
	$(MAKE) dataset-python-prepare

dataset-python-curriculum:
	$(PYTHON) -m packs.python.dataset.generate_curriculum
	$(PYTHON) -m packs.python.dataset.generate_fragments

dataset-python-collect:
	$(PYTHON_GOLD) -m packs.python.dataset.pipeline collect

dataset-python-label:
	$(PYTHON_GOLD) -m packs.python.dataset.pipeline label

dataset-python-validate:
	$(PYTHON_GOLD) -m packs.python.dataset.pipeline validate

dataset-python-prepare:
	$(PYTHON) -m training.python.prepare

test-labeling-python:
	$(PYTHON_GOLD) -m unittest discover -s packs/python/tests -v

test-training-data-shared:
	$(PYTHON) -m unittest discover -s training/shared/tests -v

train-python-smoke:
	$(PYTHON) -m training.python.train --smoke --epochs 1 --device $(PYTHON_DEVICE) $(if $(PYTHON_RUN),--output-dir "$(PYTHON_RUN)") $(if $(PYTHON_INIT_FROM),--init-from "$(PYTHON_INIT_FROM)")

train-python:
	$(PYTHON) -m training.python.train --epochs $(PYTHON_EPOCHS) --device $(PYTHON_DEVICE) --batch-size $(PYTHON_BATCH_SIZE) $(if $(PYTHON_RUN),--output-dir "$(PYTHON_RUN)") $(if $(PYTHON_INIT_FROM),--init-from "$(PYTHON_INIT_FROM)")

continue-python:
	@test -n "$(PYTHON_CHECKPOINT)" || (echo 'Set PYTHON_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.python.train --resume "$(PYTHON_CHECKPOINT)" --epochs $(PYTHON_EPOCHS) --device $(PYTHON_DEVICE)

predict-python:
	@test -n "$(PYTHON_SOURCE)" || (echo 'Set PYTHON_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.python.predict --device $(PYTHON_DEVICE) --file "$(PYTHON_SOURCE)" $(if $(PYTHON_CHECKPOINT),--checkpoint "$(PYTHON_CHECKPOINT)")

evaluate-python:
	@test -n "$(PYTHON_CHECKPOINT)" || (echo 'Set PYTHON_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.python.evaluate --checkpoint "$(PYTHON_CHECKPOINT)" --device $(PYTHON_DEVICE) --split $(PYTHON_EVAL_SPLIT)

challenge-python:
	@test -n "$(PYTHON_CHECKPOINT)" || (echo 'Set PYTHON_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.python.challenge --checkpoint "$(PYTHON_CHECKPOINT)" --device $(PYTHON_DEVICE)

export-python-model:
	@test -n "$(PYTHON_CHECKPOINT)" -a -n "$(PYTHON_TEST_REPORT)" || (echo 'Set PYTHON_CHECKPOINT and PYTHON_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.python.export_model --checkpoint "$(PYTHON_CHECKPOINT)" --test-report "$(PYTHON_TEST_REPORT)"

BASH_DEVICE ?= auto
BASH_EPOCHS ?= 3
BASH_BATCH_SIZE ?= 32
BASH_EVAL_SPLIT ?= validation

.PHONY: dataset-bash dataset-bash-sources dataset-bash-curriculum dataset-bash-collect dataset-bash-label dataset-bash-validate dataset-bash-prepare test-labeling-bash train-bash-smoke train-bash continue-bash predict-bash evaluate-bash challenge-bash export-bash-model

dataset-bash-sources:
	$(PYTHON) -m training.shared.offline_tools
	$(PYTHON) -m packs.bash.dataset.fetch_sources

dataset-bash:
	$(MAKE) dataset-bash-sources
	$(MAKE) dataset-bash-curriculum
	$(MAKE) dataset-bash-collect
	$(MAKE) dataset-bash-label
	$(MAKE) dataset-bash-validate
	$(MAKE) dataset-bash-prepare

dataset-bash-curriculum:
	$(PYTHON) -m packs.bash.dataset.generate_curriculum
	$(PYTHON) -m packs.bash.dataset.generate_fragments
	$(PYTHON) -m packs.bash.dataset.generate_programs

dataset-bash-collect:
	$(PYTHON) -m packs.bash.dataset.pipeline collect

dataset-bash-label:
	$(PYTHON) -m packs.bash.dataset.pipeline label

dataset-bash-validate:
	$(PYTHON) -m packs.bash.dataset.pipeline validate

dataset-bash-prepare:
	$(PYTHON) -m training.bash.prepare

test-labeling-bash:
	$(PYTHON) -m unittest discover -s packs/bash/tests -v

train-bash-smoke:
	$(PYTHON) -m training.bash.train --smoke --epochs 1 --device $(BASH_DEVICE) $(if $(BASH_RUN),--output-dir "$(BASH_RUN)") $(if $(BASH_INIT_FROM),--init-from "$(BASH_INIT_FROM)")

train-bash:
	$(PYTHON) -m training.bash.train --epochs $(BASH_EPOCHS) --device $(BASH_DEVICE) --batch-size $(BASH_BATCH_SIZE) $(if $(BASH_RUN),--output-dir "$(BASH_RUN)") $(if $(BASH_INIT_FROM),--init-from "$(BASH_INIT_FROM)")

continue-bash:
	@test -n "$(BASH_CHECKPOINT)" || (echo 'Set BASH_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.bash.train --resume "$(BASH_CHECKPOINT)" --epochs $(BASH_EPOCHS) --device $(BASH_DEVICE)

predict-bash:
	@test -n "$(BASH_SOURCE)" || (echo 'Set BASH_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.bash.predict --device $(BASH_DEVICE) --file "$(BASH_SOURCE)" $(if $(BASH_CHECKPOINT),--checkpoint "$(BASH_CHECKPOINT)")

evaluate-bash:
	@test -n "$(BASH_CHECKPOINT)" || (echo 'Set BASH_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.bash.evaluate --checkpoint "$(BASH_CHECKPOINT)" --device $(BASH_DEVICE) --split $(BASH_EVAL_SPLIT)

challenge-bash:
	@test -n "$(BASH_CHECKPOINT)" || (echo 'Set BASH_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.bash.challenge --checkpoint "$(BASH_CHECKPOINT)" --device $(BASH_DEVICE)

export-bash-model:
	@test -n "$(BASH_CHECKPOINT)" -a -n "$(BASH_TEST_REPORT)" || (echo 'Set BASH_CHECKPOINT and BASH_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.bash.export_model --checkpoint "$(BASH_CHECKPOINT)" --test-report "$(BASH_TEST_REPORT)"
