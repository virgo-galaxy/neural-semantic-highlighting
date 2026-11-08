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
	$(PYTHON) -m packs.bash.dataset.generate_program_fragments
	$(PYTHON) -m packs.bash.dataset.generate_arrays
	$(PYTHON) -m packs.bash.dataset.generate_heredocs
	$(PYTHON) -m packs.bash.dataset.generate_heredoc_fragments

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

PERL_DEVICE ?= auto
PERL_EPOCHS ?= 3
PERL_BATCH_SIZE ?= 32
PERL_EVAL_SPLIT ?= validation

.PHONY: dataset-perl dataset-perl-sources dataset-perl-curriculum dataset-perl-collect dataset-perl-label dataset-perl-validate dataset-perl-prepare test-labeling-perl train-perl-smoke train-perl continue-perl predict-perl evaluate-perl challenge-perl export-perl-model

dataset-perl-sources:
	$(PYTHON) -m packs.perl.dataset.fetch_sources

dataset-perl:
	$(MAKE) dataset-perl-sources
	$(MAKE) dataset-perl-curriculum
	$(MAKE) dataset-perl-collect
	$(MAKE) dataset-perl-label
	$(MAKE) dataset-perl-validate
	$(MAKE) dataset-perl-prepare

dataset-perl-curriculum:
	$(PYTHON) -m packs.perl.dataset.generate_curriculum
	$(PYTHON) -m packs.perl.dataset.generate_fragments

dataset-perl-collect:
	$(PYTHON) -m packs.perl.dataset.pipeline collect

dataset-perl-label:
	$(PYTHON) -m packs.perl.dataset.pipeline label

dataset-perl-validate:
	$(PYTHON) -m packs.perl.dataset.pipeline validate

dataset-perl-prepare:
	$(PYTHON) -m training.perl.prepare

test-labeling-perl:
	$(PYTHON) -m unittest discover -s packs/perl/tests -v

train-perl-smoke:
	$(PYTHON) -m training.perl.train --smoke --epochs 1 --device $(PERL_DEVICE) $(if $(PERL_RUN),--output-dir "$(PERL_RUN)") $(if $(PERL_INIT_FROM),--init-from "$(PERL_INIT_FROM)")

train-perl:
	$(PYTHON) -m training.perl.train --epochs $(PERL_EPOCHS) --device $(PERL_DEVICE) --batch-size $(PERL_BATCH_SIZE) $(if $(PERL_RUN),--output-dir "$(PERL_RUN)") $(if $(PERL_INIT_FROM),--init-from "$(PERL_INIT_FROM)")

continue-perl:
	@test -n "$(PERL_CHECKPOINT)" || (echo 'Set PERL_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.perl.train --resume "$(PERL_CHECKPOINT)" --epochs $(PERL_EPOCHS) --device $(PERL_DEVICE)

predict-perl:
	@test -n "$(PERL_SOURCE)" || (echo 'Set PERL_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.perl.predict --device $(PERL_DEVICE) --file "$(PERL_SOURCE)" $(if $(PERL_CHECKPOINT),--checkpoint "$(PERL_CHECKPOINT)")

evaluate-perl:
	@test -n "$(PERL_CHECKPOINT)" || (echo 'Set PERL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.perl.evaluate --checkpoint "$(PERL_CHECKPOINT)" --device $(PERL_DEVICE) --split $(PERL_EVAL_SPLIT)

challenge-perl:
	@test -n "$(PERL_CHECKPOINT)" || (echo 'Set PERL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.perl.challenge --checkpoint "$(PERL_CHECKPOINT)" --device $(PERL_DEVICE)

export-perl-model:
	@test -n "$(PERL_CHECKPOINT)" -a -n "$(PERL_TEST_REPORT)" || (echo 'Set PERL_CHECKPOINT and PERL_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.perl.export_model --checkpoint "$(PERL_CHECKPOINT)" --test-report "$(PERL_TEST_REPORT)"

AWK_DEVICE ?= auto
AWK_EPOCHS ?= 3
AWK_BATCH_SIZE ?= 32
AWK_EVAL_SPLIT ?= validation

.PHONY: dataset-awk dataset-awk-sources dataset-awk-curriculum dataset-awk-collect dataset-awk-label dataset-awk-validate dataset-awk-prepare test-labeling-awk train-awk-smoke train-awk continue-awk predict-awk evaluate-awk challenge-awk export-awk-model

dataset-awk-sources:
	$(PYTHON) -m packs.awk.dataset.fetch_sources

dataset-awk:
	$(MAKE) dataset-awk-sources
	$(MAKE) dataset-awk-curriculum
	$(MAKE) dataset-awk-collect
	$(MAKE) dataset-awk-label
	$(MAKE) dataset-awk-validate
	$(MAKE) dataset-awk-prepare

dataset-awk-curriculum:
	$(PYTHON) -m packs.awk.dataset.generate_curriculum

dataset-awk-collect:
	$(PYTHON) -m packs.awk.dataset.pipeline collect

dataset-awk-label:
	$(PYTHON) -m packs.awk.dataset.pipeline label

dataset-awk-validate:
	$(PYTHON) -m packs.awk.dataset.pipeline validate

dataset-awk-prepare:
	$(PYTHON) -m training.awk.prepare

test-labeling-awk:
	$(PYTHON) -m unittest discover -s packs/awk/tests -v

train-awk-smoke:
	$(PYTHON) -m training.awk.train --smoke --epochs 1 --device $(AWK_DEVICE) $(if $(AWK_RUN),--output-dir "$(AWK_RUN)") $(if $(AWK_INIT_FROM),--init-from "$(AWK_INIT_FROM)")

train-awk:
	$(PYTHON) -m training.awk.train --epochs $(AWK_EPOCHS) --device $(AWK_DEVICE) --batch-size $(AWK_BATCH_SIZE) $(if $(AWK_RUN),--output-dir "$(AWK_RUN)") $(if $(AWK_INIT_FROM),--init-from "$(AWK_INIT_FROM)")

continue-awk:
	@test -n "$(AWK_CHECKPOINT)" || (echo 'Set AWK_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.awk.train --resume "$(AWK_CHECKPOINT)" --epochs $(AWK_EPOCHS) --device $(AWK_DEVICE)

predict-awk:
	@test -n "$(AWK_SOURCE)" || (echo 'Set AWK_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.awk.predict --device $(AWK_DEVICE) --file "$(AWK_SOURCE)" $(if $(AWK_CHECKPOINT),--checkpoint "$(AWK_CHECKPOINT)")

evaluate-awk:
	@test -n "$(AWK_CHECKPOINT)" || (echo 'Set AWK_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.awk.evaluate --checkpoint "$(AWK_CHECKPOINT)" --device $(AWK_DEVICE) --split $(AWK_EVAL_SPLIT)

challenge-awk:
	@test -n "$(AWK_CHECKPOINT)" || (echo 'Set AWK_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.awk.challenge --checkpoint "$(AWK_CHECKPOINT)" --device $(AWK_DEVICE)

export-awk-model:
	@test -n "$(AWK_CHECKPOINT)" -a -n "$(AWK_TEST_REPORT)" || (echo 'Set AWK_CHECKPOINT and AWK_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.awk.export_model --checkpoint "$(AWK_CHECKPOINT)" --test-report "$(AWK_TEST_REPORT)"
