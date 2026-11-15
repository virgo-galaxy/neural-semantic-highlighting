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

SQL_DEVICE ?= auto
SQL_EPOCHS ?= 3
SQL_BATCH_SIZE ?= 32
SQL_EVAL_SPLIT ?= validation

.PHONY: dataset-sql dataset-sql-sources dataset-sql-curriculum dataset-sql-collect dataset-sql-label dataset-sql-validate dataset-sql-prepare test-labeling-sql train-sql-smoke train-sql continue-sql predict-sql evaluate-sql challenge-sql export-sql-model

dataset-sql-sources:
	$(PYTHON) -m packs.sql.dataset.fetch_sources

dataset-sql:
	$(MAKE) dataset-sql-sources
	$(MAKE) dataset-sql-curriculum
	$(MAKE) dataset-sql-collect
	$(MAKE) dataset-sql-label
	$(MAKE) dataset-sql-validate
	$(MAKE) dataset-sql-prepare

dataset-sql-curriculum:
	$(PYTHON) -m packs.sql.dataset.generate_curriculum
	$(PYTHON) -m packs.sql.dataset.generate_literals

dataset-sql-collect:
	$(PYTHON) -m packs.sql.dataset.pipeline collect

dataset-sql-label:
	$(PYTHON) -m packs.sql.dataset.pipeline label

dataset-sql-validate:
	$(PYTHON) -m packs.sql.dataset.pipeline validate

dataset-sql-prepare:
	$(PYTHON) -m training.sql.prepare

test-labeling-sql:
	$(PYTHON) -m unittest discover -s packs/sql/tests -v

train-sql-smoke:
	$(PYTHON) -m training.sql.train --smoke --epochs 1 --device $(SQL_DEVICE) $(if $(SQL_RUN),--output-dir "$(SQL_RUN)") $(if $(SQL_INIT_FROM),--init-from "$(SQL_INIT_FROM)")

train-sql:
	$(PYTHON) -m training.sql.train --epochs $(SQL_EPOCHS) --device $(SQL_DEVICE) --batch-size $(SQL_BATCH_SIZE) $(if $(SQL_RUN),--output-dir "$(SQL_RUN)") $(if $(SQL_INIT_FROM),--init-from "$(SQL_INIT_FROM)")

continue-sql:
	@test -n "$(SQL_CHECKPOINT)" || (echo 'Set SQL_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.sql.train --resume "$(SQL_CHECKPOINT)" --epochs $(SQL_EPOCHS) --device $(SQL_DEVICE)

predict-sql:
	@test -n "$(SQL_SOURCE)" || (echo 'Set SQL_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.sql.predict --device $(SQL_DEVICE) --file "$(SQL_SOURCE)" $(if $(SQL_CHECKPOINT),--checkpoint "$(SQL_CHECKPOINT)")

evaluate-sql:
	@test -n "$(SQL_CHECKPOINT)" || (echo 'Set SQL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.sql.evaluate --checkpoint "$(SQL_CHECKPOINT)" --device $(SQL_DEVICE) --split $(SQL_EVAL_SPLIT)

challenge-sql:
	@test -n "$(SQL_CHECKPOINT)" || (echo 'Set SQL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.sql.challenge --checkpoint "$(SQL_CHECKPOINT)" --device $(SQL_DEVICE)

export-sql-model:
	@test -n "$(SQL_CHECKPOINT)" -a -n "$(SQL_TEST_REPORT)" || (echo 'Set SQL_CHECKPOINT and SQL_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.sql.export_model --checkpoint "$(SQL_CHECKPOINT)" --test-report "$(SQL_TEST_REPORT)"

POWERSHELL_DEVICE ?= auto
POWERSHELL_EPOCHS ?= 3
POWERSHELL_BATCH_SIZE ?= 32
POWERSHELL_EVAL_SPLIT ?= validation

.PHONY: dataset-powershell dataset-powershell-sources dataset-powershell-curriculum dataset-powershell-collect dataset-powershell-label dataset-powershell-validate dataset-powershell-prepare test-labeling-powershell train-powershell-smoke train-powershell continue-powershell predict-powershell evaluate-powershell challenge-powershell export-powershell-model

dataset-powershell-sources:
	$(PYTHON) -m packs.powershell.dataset.fetch_sources

dataset-powershell:
	$(MAKE) dataset-powershell-sources
	$(MAKE) dataset-powershell-curriculum
	$(MAKE) dataset-powershell-collect
	$(MAKE) dataset-powershell-label
	$(MAKE) dataset-powershell-validate
	$(MAKE) dataset-powershell-prepare

dataset-powershell-curriculum:
	$(PYTHON) -m packs.powershell.dataset.generate_curriculum

dataset-powershell-collect:
	$(PYTHON) -m packs.powershell.dataset.pipeline collect

dataset-powershell-label:
	$(PYTHON) -m packs.powershell.dataset.pipeline label

dataset-powershell-validate:
	$(PYTHON) -m packs.powershell.dataset.pipeline validate

dataset-powershell-prepare:
	$(PYTHON) -m training.powershell.prepare

test-labeling-powershell:
	$(PYTHON) -m unittest discover -s packs/powershell/tests -v

train-powershell-smoke:
	$(PYTHON) -m training.powershell.train --smoke --epochs 1 --device $(POWERSHELL_DEVICE) $(if $(POWERSHELL_RUN),--output-dir "$(POWERSHELL_RUN)") $(if $(POWERSHELL_INIT_FROM),--init-from "$(POWERSHELL_INIT_FROM)")

train-powershell:
	$(PYTHON) -m training.powershell.train --epochs $(POWERSHELL_EPOCHS) --device $(POWERSHELL_DEVICE) --batch-size $(POWERSHELL_BATCH_SIZE) $(if $(POWERSHELL_RUN),--output-dir "$(POWERSHELL_RUN)") $(if $(POWERSHELL_INIT_FROM),--init-from "$(POWERSHELL_INIT_FROM)")

continue-powershell:
	@test -n "$(POWERSHELL_CHECKPOINT)" || (echo 'Set POWERSHELL_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.powershell.train --resume "$(POWERSHELL_CHECKPOINT)" --epochs $(POWERSHELL_EPOCHS) --device $(POWERSHELL_DEVICE)

predict-powershell:
	@test -n "$(POWERSHELL_SOURCE)" || (echo 'Set POWERSHELL_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.powershell.predict --device $(POWERSHELL_DEVICE) --file "$(POWERSHELL_SOURCE)" $(if $(POWERSHELL_CHECKPOINT),--checkpoint "$(POWERSHELL_CHECKPOINT)")

evaluate-powershell:
	@test -n "$(POWERSHELL_CHECKPOINT)" || (echo 'Set POWERSHELL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.powershell.evaluate --checkpoint "$(POWERSHELL_CHECKPOINT)" --device $(POWERSHELL_DEVICE) --split $(POWERSHELL_EVAL_SPLIT)

challenge-powershell:
	@test -n "$(POWERSHELL_CHECKPOINT)" || (echo 'Set POWERSHELL_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.powershell.challenge --checkpoint "$(POWERSHELL_CHECKPOINT)" --device $(POWERSHELL_DEVICE)

export-powershell-model:
	@test -n "$(POWERSHELL_CHECKPOINT)" -a -n "$(POWERSHELL_TEST_REPORT)" || (echo 'Set POWERSHELL_CHECKPOINT and POWERSHELL_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.powershell.export_model --checkpoint "$(POWERSHELL_CHECKPOINT)" --test-report "$(POWERSHELL_TEST_REPORT)"

BAT_DEVICE ?= auto
BAT_EPOCHS ?= 3
BAT_BATCH_SIZE ?= 32
BAT_EVAL_SPLIT ?= validation

.PHONY: dataset-bat dataset-bat-sources dataset-bat-curriculum dataset-bat-collect dataset-bat-label dataset-bat-validate dataset-bat-prepare test-labeling-bat train-bat-smoke train-bat continue-bat predict-bat evaluate-bat challenge-bat export-bat-model

dataset-bat-sources:
	$(PYTHON) -m packs.bat.dataset.fetch_sources

dataset-bat:
	$(MAKE) dataset-bat-sources
	$(MAKE) dataset-bat-curriculum
	$(MAKE) dataset-bat-collect
	$(MAKE) dataset-bat-label
	$(MAKE) dataset-bat-validate
	$(MAKE) dataset-bat-prepare

dataset-bat-curriculum:
	$(PYTHON) -m packs.bat.dataset.generate_curriculum
	$(PYTHON) -m packs.bat.dataset.generate_fragments

dataset-bat-collect:
	$(PYTHON) -m packs.bat.dataset.pipeline collect

dataset-bat-label:
	$(PYTHON) -m packs.bat.dataset.pipeline label

dataset-bat-validate:
	$(PYTHON) -m packs.bat.dataset.pipeline validate

dataset-bat-prepare:
	$(PYTHON) -m training.bat.prepare

test-labeling-bat:
	$(PYTHON) -m unittest discover -s packs/bat/tests -v

train-bat-smoke:
	$(PYTHON) -m training.bat.train --smoke --epochs 1 --device $(BAT_DEVICE) $(if $(BAT_RUN),--output-dir "$(BAT_RUN)") $(if $(BAT_INIT_FROM),--init-from "$(BAT_INIT_FROM)")

train-bat:
	$(PYTHON) -m training.bat.train --epochs $(BAT_EPOCHS) --device $(BAT_DEVICE) --batch-size $(BAT_BATCH_SIZE) $(if $(BAT_RUN),--output-dir "$(BAT_RUN)") $(if $(BAT_INIT_FROM),--init-from "$(BAT_INIT_FROM)")

continue-bat:
	@test -n "$(BAT_CHECKPOINT)" || (echo 'Set BAT_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.bat.train --resume "$(BAT_CHECKPOINT)" --epochs $(BAT_EPOCHS) --device $(BAT_DEVICE)

predict-bat:
	@test -n "$(BAT_SOURCE)" || (echo 'Set BAT_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.bat.predict --device $(BAT_DEVICE) --file "$(BAT_SOURCE)" $(if $(BAT_CHECKPOINT),--checkpoint "$(BAT_CHECKPOINT)")

evaluate-bat:
	@test -n "$(BAT_CHECKPOINT)" || (echo 'Set BAT_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.bat.evaluate --checkpoint "$(BAT_CHECKPOINT)" --device $(BAT_DEVICE) --split $(BAT_EVAL_SPLIT)

challenge-bat:
	@test -n "$(BAT_CHECKPOINT)" || (echo 'Set BAT_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.bat.challenge --checkpoint "$(BAT_CHECKPOINT)" --device $(BAT_DEVICE)

export-bat-model:
	@test -n "$(BAT_CHECKPOINT)" -a -n "$(BAT_TEST_REPORT)" || (echo 'Set BAT_CHECKPOINT and BAT_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.bat.export_model --checkpoint "$(BAT_CHECKPOINT)" --test-report "$(BAT_TEST_REPORT)"

ASSEMBLY_DEVICE ?= auto
ASSEMBLY_EPOCHS ?= 3
ASSEMBLY_BATCH_SIZE ?= 32
ASSEMBLY_EVAL_SPLIT ?= validation

.PHONY: dataset-assembly dataset-assembly-sources dataset-assembly-curriculum dataset-assembly-collect dataset-assembly-label dataset-assembly-validate dataset-assembly-prepare test-labeling-assembly train-assembly-smoke train-assembly continue-assembly predict-assembly evaluate-assembly challenge-assembly export-assembly-model

dataset-assembly-sources:
	$(PYTHON) -m training.shared.offline_tools
	$(PYTHON) -m packs.assembly.dataset.fetch_sources

dataset-assembly:
	$(MAKE) dataset-assembly-sources
	$(MAKE) dataset-assembly-curriculum
	$(MAKE) dataset-assembly-collect
	$(MAKE) dataset-assembly-label
	$(MAKE) dataset-assembly-validate
	$(MAKE) dataset-assembly-prepare

dataset-assembly-curriculum:
	$(PYTHON) -m packs.assembly.dataset.generate_curriculum

dataset-assembly-collect:
	$(PYTHON) -m packs.assembly.dataset.pipeline collect

dataset-assembly-label:
	$(PYTHON) -m packs.assembly.dataset.pipeline label

dataset-assembly-validate:
	$(PYTHON) -m packs.assembly.dataset.pipeline validate

dataset-assembly-prepare:
	$(PYTHON) -m training.assembly.prepare

test-labeling-assembly:
	$(PYTHON) -m unittest discover -s packs/assembly/tests -v

train-assembly-smoke:
	$(PYTHON) -m training.assembly.train --smoke --epochs 1 --device $(ASSEMBLY_DEVICE) $(if $(ASSEMBLY_RUN),--output-dir "$(ASSEMBLY_RUN)") $(if $(ASSEMBLY_INIT_FROM),--init-from "$(ASSEMBLY_INIT_FROM)")

train-assembly:
	$(PYTHON) -m training.assembly.train --epochs $(ASSEMBLY_EPOCHS) --device $(ASSEMBLY_DEVICE) --batch-size $(ASSEMBLY_BATCH_SIZE) $(if $(ASSEMBLY_RUN),--output-dir "$(ASSEMBLY_RUN)") $(if $(ASSEMBLY_INIT_FROM),--init-from "$(ASSEMBLY_INIT_FROM)")

continue-assembly:
	@test -n "$(ASSEMBLY_CHECKPOINT)" || (echo 'Set ASSEMBLY_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.assembly.train --resume "$(ASSEMBLY_CHECKPOINT)" --epochs $(ASSEMBLY_EPOCHS) --device $(ASSEMBLY_DEVICE)

predict-assembly:
	@test -n "$(ASSEMBLY_SOURCE)" || (echo 'Set ASSEMBLY_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.assembly.predict --device $(ASSEMBLY_DEVICE) --file "$(ASSEMBLY_SOURCE)" $(if $(ASSEMBLY_CHECKPOINT),--checkpoint "$(ASSEMBLY_CHECKPOINT)")

evaluate-assembly:
	@test -n "$(ASSEMBLY_CHECKPOINT)" || (echo 'Set ASSEMBLY_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.assembly.evaluate --checkpoint "$(ASSEMBLY_CHECKPOINT)" --device $(ASSEMBLY_DEVICE) --split $(ASSEMBLY_EVAL_SPLIT)

challenge-assembly:
	@test -n "$(ASSEMBLY_CHECKPOINT)" || (echo 'Set ASSEMBLY_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.assembly.challenge --checkpoint "$(ASSEMBLY_CHECKPOINT)" --device $(ASSEMBLY_DEVICE)

export-assembly-model:
	@test -n "$(ASSEMBLY_CHECKPOINT)" -a -n "$(ASSEMBLY_TEST_REPORT)" || (echo 'Set ASSEMBLY_CHECKPOINT and ASSEMBLY_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.assembly.export_model --checkpoint "$(ASSEMBLY_CHECKPOINT)" --test-report "$(ASSEMBLY_TEST_REPORT)"

JAVA_DEVICE ?= auto
JAVA_EPOCHS ?= 3
JAVA_BATCH_SIZE ?= 32
JAVA_LEARNING_RATE ?=
JAVA_EVAL_SPLIT ?= validation

.PHONY: dataset-java dataset-java-sources dataset-java-curriculum dataset-java-collect dataset-java-label dataset-java-validate dataset-java-prepare test-labeling-java train-java-smoke train-java continue-java predict-java evaluate-java challenge-java export-java-model

dataset-java-sources:
	$(PYTHON) -m packs.java.dataset.fetch_sources
	$(PYTHON) -m packs.java.dataset.capture_jdk

dataset-java:
	$(MAKE) dataset-java-sources
	$(MAKE) dataset-java-curriculum
	$(MAKE) dataset-java-collect
	$(MAKE) dataset-java-label
	$(MAKE) dataset-java-validate
	$(MAKE) dataset-java-prepare

dataset-java-curriculum:
	$(PYTHON) -m packs.java.dataset.generate_curriculum
	$(PYTHON) -m packs.java.dataset.generate_mixed

dataset-java-collect:
	$(PYTHON) -m packs.java.dataset.pipeline collect

dataset-java-label:
	$(PYTHON) -m packs.java.dataset.pipeline label

dataset-java-validate:
	$(PYTHON) -m packs.java.dataset.pipeline validate

dataset-java-prepare:
	$(PYTHON) -m training.java.prepare

test-labeling-java:
	$(PYTHON) -m unittest discover -s packs/java/tests -v

train-java-smoke:
	$(PYTHON) -m training.java.train --smoke --epochs 1 --device $(JAVA_DEVICE) $(if $(JAVA_RUN),--output-dir "$(JAVA_RUN)") $(if $(JAVA_INIT_FROM),--init-from "$(JAVA_INIT_FROM)")

train-java:
	$(PYTHON) -m training.java.train --epochs $(JAVA_EPOCHS) --device $(JAVA_DEVICE) --batch-size $(JAVA_BATCH_SIZE) $(if $(JAVA_LEARNING_RATE),--learning-rate $(JAVA_LEARNING_RATE)) $(if $(JAVA_RUN),--output-dir "$(JAVA_RUN)") $(if $(JAVA_INIT_FROM),--init-from "$(JAVA_INIT_FROM)")

continue-java:
	@test -n "$(JAVA_CHECKPOINT)" || (echo 'Set JAVA_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.java.train --resume "$(JAVA_CHECKPOINT)" --epochs $(JAVA_EPOCHS) --device $(JAVA_DEVICE)

predict-java:
	@test -n "$(JAVA_SOURCE)" || (echo 'Set JAVA_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.java.predict --device $(JAVA_DEVICE) --file "$(JAVA_SOURCE)" $(if $(JAVA_CHECKPOINT),--checkpoint "$(JAVA_CHECKPOINT)")

evaluate-java:
	@test -n "$(JAVA_CHECKPOINT)" || (echo 'Set JAVA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.java.evaluate --checkpoint "$(JAVA_CHECKPOINT)" --device $(JAVA_DEVICE) --split $(JAVA_EVAL_SPLIT)

challenge-java:
	@test -n "$(JAVA_CHECKPOINT)" || (echo 'Set JAVA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.java.challenge --checkpoint "$(JAVA_CHECKPOINT)" --device $(JAVA_DEVICE)

export-java-model:
	@test -n "$(JAVA_CHECKPOINT)" -a -n "$(JAVA_TEST_REPORT)" || (echo 'Set JAVA_CHECKPOINT and JAVA_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.java.export_model --checkpoint "$(JAVA_CHECKPOINT)" --test-report "$(JAVA_TEST_REPORT)"

CSHARP_DEVICE ?= auto
CSHARP_EPOCHS ?= 3
CSHARP_BATCH_SIZE ?= 32
CSHARP_LEARNING_RATE ?=
CSHARP_EVAL_SPLIT ?= validation

.PHONY: dataset-csharp dataset-csharp-tools dataset-csharp-sources dataset-csharp-curriculum dataset-csharp-collect dataset-csharp-label dataset-csharp-validate dataset-csharp-prepare test-labeling-csharp train-csharp-smoke train-csharp continue-csharp predict-csharp evaluate-csharp challenge-csharp export-csharp-model

dataset-csharp-tools:
	$(PYTHON) -m packs.csharp.labeling.tools

dataset-csharp-sources:
	$(PYTHON) -m packs.csharp.dataset.fetch_sources

dataset-csharp:
	$(MAKE) dataset-csharp-tools
	$(MAKE) dataset-csharp-sources
	$(MAKE) dataset-csharp-curriculum
	$(MAKE) dataset-csharp-collect
	$(MAKE) dataset-csharp-label
	$(MAKE) dataset-csharp-validate
	$(MAKE) dataset-csharp-prepare

dataset-csharp-curriculum:
	$(PYTHON) -m packs.csharp.dataset.generate_curriculum
	$(PYTHON) -m packs.csharp.dataset.generate_mixed

dataset-csharp-collect:
	$(PYTHON) -m packs.csharp.dataset.pipeline collect

dataset-csharp-label:
	$(PYTHON) -m packs.csharp.dataset.pipeline label

dataset-csharp-validate:
	$(PYTHON) -m packs.csharp.dataset.pipeline validate

dataset-csharp-prepare:
	$(PYTHON) -m training.csharp.prepare

test-labeling-csharp:
	$(PYTHON) -m unittest discover -s packs/csharp/tests -v

train-csharp-smoke:
	$(PYTHON) -m training.csharp.train --smoke --epochs 1 --device $(CSHARP_DEVICE) $(if $(CSHARP_RUN),--output-dir "$(CSHARP_RUN)") $(if $(CSHARP_INIT_FROM),--init-from "$(CSHARP_INIT_FROM)")

train-csharp:
	$(PYTHON) -m training.csharp.train --epochs $(CSHARP_EPOCHS) --device $(CSHARP_DEVICE) --batch-size $(CSHARP_BATCH_SIZE) $(if $(CSHARP_LEARNING_RATE),--learning-rate $(CSHARP_LEARNING_RATE)) $(if $(CSHARP_RUN),--output-dir "$(CSHARP_RUN)") $(if $(CSHARP_INIT_FROM),--init-from "$(CSHARP_INIT_FROM)")

continue-csharp:
	@test -n "$(CSHARP_CHECKPOINT)" || (echo 'Set CSHARP_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.csharp.train --resume "$(CSHARP_CHECKPOINT)" --epochs $(CSHARP_EPOCHS) --device $(CSHARP_DEVICE)

predict-csharp:
	@test -n "$(CSHARP_SOURCE)" || (echo 'Set CSHARP_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.csharp.predict --device $(CSHARP_DEVICE) --file "$(CSHARP_SOURCE)" $(if $(CSHARP_CHECKPOINT),--checkpoint "$(CSHARP_CHECKPOINT)")

evaluate-csharp:
	@test -n "$(CSHARP_CHECKPOINT)" || (echo 'Set CSHARP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.csharp.evaluate --checkpoint "$(CSHARP_CHECKPOINT)" --device $(CSHARP_DEVICE) --split $(CSHARP_EVAL_SPLIT)

challenge-csharp:
	@test -n "$(CSHARP_CHECKPOINT)" || (echo 'Set CSHARP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.csharp.challenge --checkpoint "$(CSHARP_CHECKPOINT)" --device $(CSHARP_DEVICE)

export-csharp-model:
	@test -n "$(CSHARP_CHECKPOINT)" -a -n "$(CSHARP_TEST_REPORT)" || (echo 'Set CSHARP_CHECKPOINT and CSHARP_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.csharp.export_model --checkpoint "$(CSHARP_CHECKPOINT)" --test-report "$(CSHARP_TEST_REPORT)"

C_DEVICE ?= auto
C_EPOCHS ?= 3
C_BATCH_SIZE ?= 32
C_LEARNING_RATE ?=
C_EVAL_SPLIT ?= validation

.PHONY: dataset-c dataset-c-tools dataset-c-sources dataset-c-curriculum dataset-c-collect dataset-c-label dataset-c-validate dataset-c-prepare test-labeling-c train-c-smoke train-c continue-c predict-c evaluate-c challenge-c export-c-model

dataset-c-tools:
	$(PYTHON) -m packs.c.labeling.tools

dataset-c-sources:
	$(PYTHON) -m packs.c.dataset.fetch_sources

dataset-c:
	$(MAKE) dataset-c-tools
	$(MAKE) dataset-c-sources
	$(MAKE) dataset-c-curriculum
	$(MAKE) dataset-c-collect
	$(MAKE) dataset-c-label
	$(MAKE) dataset-c-validate
	$(MAKE) dataset-c-prepare

dataset-c-curriculum:
	$(PYTHON) -m packs.c.dataset.generate_curriculum
	$(PYTHON) -m packs.c.dataset.generate_mixed

dataset-c-collect:
	$(PYTHON) -m packs.c.dataset.pipeline collect

dataset-c-label:
	$(PYTHON) -m packs.c.dataset.pipeline label

dataset-c-validate:
	$(PYTHON) -m packs.c.dataset.pipeline validate

dataset-c-prepare:
	$(PYTHON) -m training.c.prepare

test-labeling-c:
	$(PYTHON) -m unittest discover -s packs/c/tests -v

train-c-smoke:
	$(PYTHON) -m training.c.train --smoke --epochs 1 --device $(C_DEVICE) $(if $(C_RUN),--output-dir "$(C_RUN)") $(if $(C_INIT_FROM),--init-from "$(C_INIT_FROM)")

train-c:
	$(PYTHON) -m training.c.train --epochs $(C_EPOCHS) --device $(C_DEVICE) --batch-size $(C_BATCH_SIZE) $(if $(C_LEARNING_RATE),--learning-rate $(C_LEARNING_RATE)) $(if $(C_RUN),--output-dir "$(C_RUN)") $(if $(C_INIT_FROM),--init-from "$(C_INIT_FROM)")

continue-c:
	@test -n "$(C_CHECKPOINT)" || (echo 'Set C_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.c.train --resume "$(C_CHECKPOINT)" --epochs $(C_EPOCHS) --device $(C_DEVICE)

predict-c:
	@test -n "$(C_SOURCE)" || (echo 'Set C_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.c.predict --device $(C_DEVICE) --file "$(C_SOURCE)" $(if $(C_CHECKPOINT),--checkpoint "$(C_CHECKPOINT)")

evaluate-c:
	@test -n "$(C_CHECKPOINT)" || (echo 'Set C_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.c.evaluate --checkpoint "$(C_CHECKPOINT)" --device $(C_DEVICE) --split $(C_EVAL_SPLIT)

challenge-c:
	@test -n "$(C_CHECKPOINT)" || (echo 'Set C_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.c.challenge --checkpoint "$(C_CHECKPOINT)" --device $(C_DEVICE)

export-c-model:
	@test -n "$(C_CHECKPOINT)" -a -n "$(C_TEST_REPORT)" || (echo 'Set C_CHECKPOINT and C_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.c.export_model --checkpoint "$(C_CHECKPOINT)" --test-report "$(C_TEST_REPORT)"

CPP_DEVICE ?= auto
CPP_EPOCHS ?= 3
CPP_BATCH_SIZE ?= 32
CPP_LEARNING_RATE ?=
CPP_EVAL_SPLIT ?= validation

.PHONY: dataset-cpp dataset-cpp-tools dataset-cpp-sources dataset-cpp-curriculum dataset-cpp-collect dataset-cpp-label dataset-cpp-validate dataset-cpp-prepare test-labeling-cpp train-cpp-smoke train-cpp continue-cpp predict-cpp evaluate-cpp challenge-cpp export-cpp-model

dataset-cpp-tools:
	$(PYTHON) -m packs.cpp.labeling.tools

dataset-cpp-sources:
	$(PYTHON) -m packs.cpp.dataset.fetch_sources

dataset-cpp:
	$(MAKE) dataset-cpp-tools
	$(MAKE) dataset-cpp-sources
	$(MAKE) dataset-cpp-curriculum
	$(MAKE) dataset-cpp-collect
	$(MAKE) dataset-cpp-label
	$(MAKE) dataset-cpp-validate
	$(MAKE) dataset-cpp-prepare

dataset-cpp-curriculum:
	$(PYTHON) -m packs.cpp.dataset.generate_curriculum
	$(PYTHON) -m packs.cpp.dataset.generate_mixed

dataset-cpp-collect:
	$(PYTHON) -m packs.cpp.dataset.pipeline collect

dataset-cpp-label:
	$(PYTHON) -m packs.cpp.dataset.pipeline label

dataset-cpp-validate:
	$(PYTHON) -m packs.cpp.dataset.pipeline validate

dataset-cpp-prepare:
	$(PYTHON) -m training.cpp.prepare

test-labeling-cpp:
	$(PYTHON) -m unittest discover -s packs/cpp/tests -v

train-cpp-smoke:
	$(PYTHON) -m training.cpp.train --smoke --epochs 1 --device $(CPP_DEVICE) $(if $(CPP_RUN),--output-dir "$(CPP_RUN)") $(if $(CPP_INIT_FROM),--init-from "$(CPP_INIT_FROM)")

train-cpp:
	$(PYTHON) -m training.cpp.train --epochs $(CPP_EPOCHS) --device $(CPP_DEVICE) --batch-size $(CPP_BATCH_SIZE) $(if $(CPP_LEARNING_RATE),--learning-rate $(CPP_LEARNING_RATE)) $(if $(CPP_RUN),--output-dir "$(CPP_RUN)") $(if $(CPP_INIT_FROM),--init-from "$(CPP_INIT_FROM)")

continue-cpp:
	@test -n "$(CPP_CHECKPOINT)" || (echo 'Set CPP_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.cpp.train --resume "$(CPP_CHECKPOINT)" --epochs $(CPP_EPOCHS) --device $(CPP_DEVICE)

predict-cpp:
	@test -n "$(CPP_SOURCE)" || (echo 'Set CPP_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.cpp.predict --device $(CPP_DEVICE) --file "$(CPP_SOURCE)" $(if $(CPP_CHECKPOINT),--checkpoint "$(CPP_CHECKPOINT)")

evaluate-cpp:
	@test -n "$(CPP_CHECKPOINT)" || (echo 'Set CPP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.cpp.evaluate --checkpoint "$(CPP_CHECKPOINT)" --device $(CPP_DEVICE) --split $(CPP_EVAL_SPLIT)

challenge-cpp:
	@test -n "$(CPP_CHECKPOINT)" || (echo 'Set CPP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.cpp.challenge --checkpoint "$(CPP_CHECKPOINT)" --device $(CPP_DEVICE)

export-cpp-model:
	@test -n "$(CPP_CHECKPOINT)" -a -n "$(CPP_TEST_REPORT)" || (echo 'Set CPP_CHECKPOINT and CPP_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.cpp.export_model --checkpoint "$(CPP_CHECKPOINT)" --test-report "$(CPP_TEST_REPORT)"

PHP_DEVICE ?= auto
PHP_EPOCHS ?= 3
PHP_BATCH_SIZE ?= 32
PHP_LEARNING_RATE ?=
PHP_EVAL_SPLIT ?= validation

.PHONY: dataset-php dataset-php-tools dataset-php-sources dataset-php-curriculum dataset-php-collect dataset-php-label dataset-php-validate dataset-php-prepare test-labeling-php train-php-smoke train-php continue-php predict-php evaluate-php challenge-php export-php-model

dataset-php-tools:
	$(PYTHON) -m packs.php.labeling.tools

dataset-php-sources:
	$(PYTHON) -m packs.php.dataset.fetch_sources

dataset-php:
	$(MAKE) dataset-php-tools
	$(MAKE) dataset-php-sources
	$(MAKE) dataset-php-curriculum
	$(MAKE) dataset-php-collect
	$(MAKE) dataset-php-label
	$(MAKE) dataset-php-validate
	$(MAKE) dataset-php-prepare

dataset-php-curriculum:
	$(PYTHON) -m packs.php.dataset.generate_curriculum
	$(PYTHON) -m packs.php.dataset.generate_mixed

dataset-php-collect:
	$(PYTHON) -m packs.php.dataset.pipeline collect

dataset-php-label:
	$(PYTHON) -m packs.php.dataset.pipeline label

dataset-php-validate:
	$(PYTHON) -m packs.php.dataset.pipeline validate

dataset-php-prepare:
	$(PYTHON) -m training.php.prepare

test-labeling-php:
	$(PYTHON) -m unittest discover -s packs/php/tests -v

train-php-smoke:
	$(PYTHON) -m training.php.train --smoke --epochs 1 --device $(PHP_DEVICE) $(if $(PHP_RUN),--output-dir "$(PHP_RUN)") $(if $(PHP_INIT_FROM),--init-from "$(PHP_INIT_FROM)")

train-php:
	$(PYTHON) -m training.php.train --epochs $(PHP_EPOCHS) --device $(PHP_DEVICE) --batch-size $(PHP_BATCH_SIZE) $(if $(PHP_LEARNING_RATE),--learning-rate $(PHP_LEARNING_RATE)) $(if $(PHP_RUN),--output-dir "$(PHP_RUN)") $(if $(PHP_INIT_FROM),--init-from "$(PHP_INIT_FROM)")

continue-php:
	@test -n "$(PHP_CHECKPOINT)" || (echo 'Set PHP_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.php.train --resume "$(PHP_CHECKPOINT)" --epochs $(PHP_EPOCHS) --device $(PHP_DEVICE)

predict-php:
	@test -n "$(PHP_SOURCE)" || (echo 'Set PHP_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.php.predict --device $(PHP_DEVICE) --file "$(PHP_SOURCE)" $(if $(PHP_CHECKPOINT),--checkpoint "$(PHP_CHECKPOINT)")

evaluate-php:
	@test -n "$(PHP_CHECKPOINT)" || (echo 'Set PHP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.php.evaluate --checkpoint "$(PHP_CHECKPOINT)" --device $(PHP_DEVICE) --split $(PHP_EVAL_SPLIT)

challenge-php:
	@test -n "$(PHP_CHECKPOINT)" || (echo 'Set PHP_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.php.challenge --checkpoint "$(PHP_CHECKPOINT)" --device $(PHP_DEVICE)

export-php-model:
	@test -n "$(PHP_CHECKPOINT)" -a -n "$(PHP_TEST_REPORT)" || (echo 'Set PHP_CHECKPOINT and PHP_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.php.export_model --checkpoint "$(PHP_CHECKPOINT)" --test-report "$(PHP_TEST_REPORT)"

SVELTE_DEVICE ?= auto
SVELTE_EPOCHS ?= 3
SVELTE_BATCH_SIZE ?= 32
SVELTE_LEARNING_RATE ?=
SVELTE_EVAL_SPLIT ?= validation

.PHONY: dataset-svelte dataset-svelte-tools dataset-svelte-sources dataset-svelte-curriculum dataset-svelte-collect dataset-svelte-label dataset-svelte-validate dataset-svelte-prepare test-labeling-svelte train-svelte-smoke train-svelte continue-svelte predict-svelte evaluate-svelte challenge-svelte export-svelte-model

dataset-svelte-tools:
	$(PYTHON) -m packs.svelte.labeling.tools

dataset-svelte-sources:
	$(PYTHON) -m packs.svelte.dataset.fetch_sources

dataset-svelte:
	$(MAKE) dataset-svelte-tools
	$(MAKE) dataset-svelte-sources
	$(MAKE) dataset-svelte-curriculum
	$(MAKE) dataset-svelte-collect
	$(MAKE) dataset-svelte-label
	$(MAKE) dataset-svelte-validate
	$(MAKE) dataset-svelte-prepare

dataset-svelte-curriculum:
	$(PYTHON) -m packs.svelte.dataset.generate_curriculum
	$(PYTHON) -m packs.svelte.dataset.generate_boundaries

dataset-svelte-collect:
	$(PYTHON) -m packs.svelte.dataset.pipeline collect

dataset-svelte-label:
	$(PYTHON) -m packs.svelte.dataset.pipeline label

dataset-svelte-validate:
	$(PYTHON) -m packs.svelte.dataset.pipeline validate

dataset-svelte-prepare:
	$(PYTHON) -m training.svelte.prepare

test-labeling-svelte:
	$(PYTHON) -m unittest discover -s packs/svelte/tests -v

train-svelte-smoke:
	$(PYTHON) -m training.svelte.train --smoke --epochs 1 --device $(SVELTE_DEVICE) $(if $(SVELTE_RUN),--output-dir "$(SVELTE_RUN)") $(if $(SVELTE_INIT_FROM),--init-from "$(SVELTE_INIT_FROM)")

train-svelte:
	$(PYTHON) -m training.svelte.train --epochs $(SVELTE_EPOCHS) --device $(SVELTE_DEVICE) --batch-size $(SVELTE_BATCH_SIZE) $(if $(SVELTE_LEARNING_RATE),--learning-rate $(SVELTE_LEARNING_RATE)) $(if $(SVELTE_RUN),--output-dir "$(SVELTE_RUN)") $(if $(SVELTE_INIT_FROM),--init-from "$(SVELTE_INIT_FROM)")

continue-svelte:
	@test -n "$(SVELTE_CHECKPOINT)" || (echo 'Set SVELTE_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.svelte.train --resume "$(SVELTE_CHECKPOINT)" --epochs $(SVELTE_EPOCHS) --device $(SVELTE_DEVICE)

predict-svelte:
	@test -n "$(SVELTE_SOURCE)" || (echo 'Set SVELTE_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.svelte.predict --device $(SVELTE_DEVICE) --file "$(SVELTE_SOURCE)" $(if $(SVELTE_CHECKPOINT),--checkpoint "$(SVELTE_CHECKPOINT)")

evaluate-svelte:
	@test -n "$(SVELTE_CHECKPOINT)" || (echo 'Set SVELTE_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.svelte.evaluate --checkpoint "$(SVELTE_CHECKPOINT)" --device $(SVELTE_DEVICE) --split $(SVELTE_EVAL_SPLIT)

challenge-svelte:
	@test -n "$(SVELTE_CHECKPOINT)" || (echo 'Set SVELTE_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.svelte.challenge --checkpoint "$(SVELTE_CHECKPOINT)" --device $(SVELTE_DEVICE)

export-svelte-model:
	@test -n "$(SVELTE_CHECKPOINT)" -a -n "$(SVELTE_TEST_REPORT)" || (echo 'Set SVELTE_CHECKPOINT and SVELTE_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.svelte.export_model --checkpoint "$(SVELTE_CHECKPOINT)" --test-report "$(SVELTE_TEST_REPORT)"

RUST_DEVICE ?= auto
RUST_EPOCHS ?= 3
RUST_BATCH_SIZE ?= 32
RUST_LEARNING_RATE ?=
RUST_EVAL_SPLIT ?= validation

.PHONY: dataset-rust dataset-rust-tools dataset-rust-sources dataset-rust-curriculum dataset-rust-collect dataset-rust-label dataset-rust-validate dataset-rust-prepare test-labeling-rust train-rust-smoke train-rust continue-rust predict-rust evaluate-rust challenge-rust export-rust-model

dataset-rust-tools:
	$(PYTHON) -m packs.rust.labeling.tools

dataset-rust-sources:
	$(PYTHON) -m packs.rust.dataset.fetch_sources

dataset-rust:
	$(MAKE) dataset-rust-tools
	$(MAKE) dataset-rust-sources
	$(MAKE) dataset-rust-curriculum
	$(MAKE) dataset-rust-collect
	$(MAKE) dataset-rust-label
	$(MAKE) dataset-rust-validate
	$(MAKE) dataset-rust-prepare

dataset-rust-curriculum:
	$(PYTHON) -m packs.rust.dataset.generate_curriculum
	$(PYTHON) -m packs.rust.dataset.generate_literals

dataset-rust-collect:
	$(PYTHON) -m packs.rust.dataset.pipeline collect

dataset-rust-label:
	$(PYTHON) -m packs.rust.dataset.pipeline label

dataset-rust-validate:
	$(PYTHON) -m packs.rust.dataset.pipeline validate

dataset-rust-prepare:
	$(PYTHON) -m training.rust.prepare

test-labeling-rust:
	$(PYTHON) -m unittest discover -s packs/rust/tests -v

train-rust-smoke:
	$(PYTHON) -m training.rust.train --smoke --epochs 1 --device $(RUST_DEVICE) $(if $(RUST_RUN),--output-dir "$(RUST_RUN)") $(if $(RUST_INIT_FROM),--init-from "$(RUST_INIT_FROM)")

train-rust:
	$(PYTHON) -m training.rust.train --epochs $(RUST_EPOCHS) --device $(RUST_DEVICE) --batch-size $(RUST_BATCH_SIZE) $(if $(RUST_LEARNING_RATE),--learning-rate $(RUST_LEARNING_RATE)) $(if $(RUST_RUN),--output-dir "$(RUST_RUN)") $(if $(RUST_INIT_FROM),--init-from "$(RUST_INIT_FROM)")

continue-rust:
	@test -n "$(RUST_CHECKPOINT)" || (echo 'Set RUST_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.rust.train --resume "$(RUST_CHECKPOINT)" --epochs $(RUST_EPOCHS) --device $(RUST_DEVICE)

predict-rust:
	@test -n "$(RUST_SOURCE)" || (echo 'Set RUST_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.rust.predict --device $(RUST_DEVICE) --file "$(RUST_SOURCE)" $(if $(RUST_CHECKPOINT),--checkpoint "$(RUST_CHECKPOINT)")

evaluate-rust:
	@test -n "$(RUST_CHECKPOINT)" || (echo 'Set RUST_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.rust.evaluate --checkpoint "$(RUST_CHECKPOINT)" --device $(RUST_DEVICE) --split $(RUST_EVAL_SPLIT)

challenge-rust:
	@test -n "$(RUST_CHECKPOINT)" || (echo 'Set RUST_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.rust.challenge --checkpoint "$(RUST_CHECKPOINT)" --device $(RUST_DEVICE)

export-rust-model:
	@test -n "$(RUST_CHECKPOINT)" -a -n "$(RUST_TEST_REPORT)" || (echo 'Set RUST_CHECKPOINT and RUST_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.rust.export_model --checkpoint "$(RUST_CHECKPOINT)" --test-report "$(RUST_TEST_REPORT)"

ZIG_DEVICE ?= auto
ZIG_EPOCHS ?= 3
ZIG_BATCH_SIZE ?= 32
ZIG_LEARNING_RATE ?=
ZIG_EVAL_SPLIT ?= validation

.PHONY: dataset-zig dataset-zig-tools dataset-zig-sources dataset-zig-curriculum dataset-zig-collect dataset-zig-label dataset-zig-validate dataset-zig-prepare test-labeling-zig train-zig-smoke train-zig continue-zig predict-zig evaluate-zig challenge-zig export-zig-model

dataset-zig-tools:
	$(PYTHON) -m packs.zig.labeling.tools

dataset-zig-sources:
	$(PYTHON) -m packs.zig.dataset.fetch_sources

dataset-zig:
	$(MAKE) dataset-zig-tools
	$(MAKE) dataset-zig-sources
	$(MAKE) dataset-zig-curriculum
	$(MAKE) dataset-zig-collect
	$(MAKE) dataset-zig-label
	$(MAKE) dataset-zig-validate
	$(MAKE) dataset-zig-prepare

dataset-zig-curriculum:
	$(PYTHON) -m packs.zig.dataset.generate_curriculum

dataset-zig-collect:
	$(PYTHON) -m packs.zig.dataset.pipeline collect

dataset-zig-label:
	$(PYTHON) -m packs.zig.dataset.pipeline label

dataset-zig-validate:
	$(PYTHON) -m packs.zig.dataset.pipeline validate

dataset-zig-prepare:
	$(PYTHON) -m training.zig.prepare

test-labeling-zig:
	$(PYTHON) -m unittest discover -s packs/zig/tests -v

train-zig-smoke:
	$(PYTHON) -m training.zig.train --smoke --epochs 1 --device $(ZIG_DEVICE) $(if $(ZIG_RUN),--output-dir "$(ZIG_RUN)") $(if $(ZIG_INIT_FROM),--init-from "$(ZIG_INIT_FROM)")

train-zig:
	$(PYTHON) -m training.zig.train --epochs $(ZIG_EPOCHS) --device $(ZIG_DEVICE) --batch-size $(ZIG_BATCH_SIZE) $(if $(ZIG_LEARNING_RATE),--learning-rate $(ZIG_LEARNING_RATE)) $(if $(ZIG_RUN),--output-dir "$(ZIG_RUN)") $(if $(ZIG_INIT_FROM),--init-from "$(ZIG_INIT_FROM)")

continue-zig:
	@test -n "$(ZIG_CHECKPOINT)" || (echo 'Set ZIG_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.zig.train --resume "$(ZIG_CHECKPOINT)" --epochs $(ZIG_EPOCHS) --device $(ZIG_DEVICE)

predict-zig:
	@test -n "$(ZIG_SOURCE)" || (echo 'Set ZIG_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.zig.predict --device $(ZIG_DEVICE) --file "$(ZIG_SOURCE)" $(if $(ZIG_CHECKPOINT),--checkpoint "$(ZIG_CHECKPOINT)")

evaluate-zig:
	@test -n "$(ZIG_CHECKPOINT)" || (echo 'Set ZIG_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.zig.evaluate --checkpoint "$(ZIG_CHECKPOINT)" --device $(ZIG_DEVICE) --split $(ZIG_EVAL_SPLIT)

challenge-zig:
	@test -n "$(ZIG_CHECKPOINT)" || (echo 'Set ZIG_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.zig.challenge --checkpoint "$(ZIG_CHECKPOINT)" --device $(ZIG_DEVICE)

export-zig-model:
	@test -n "$(ZIG_CHECKPOINT)" -a -n "$(ZIG_TEST_REPORT)" || (echo 'Set ZIG_CHECKPOINT and ZIG_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.zig.export_model --checkpoint "$(ZIG_CHECKPOINT)" --test-report "$(ZIG_TEST_REPORT)"

DART_DEVICE ?= auto
DART_EPOCHS ?= 3
DART_BATCH_SIZE ?= 32
DART_LEARNING_RATE ?=
DART_EVAL_SPLIT ?= validation

.PHONY: dataset-dart dataset-dart-tools dataset-dart-sources dataset-dart-curriculum dataset-dart-collect dataset-dart-label dataset-dart-validate dataset-dart-prepare test-labeling-dart train-dart-smoke train-dart continue-dart predict-dart evaluate-dart challenge-dart export-dart-model

dataset-dart-tools:
	$(PYTHON) -m packs.dart.labeling.tools

dataset-dart-sources:
	$(PYTHON) -m packs.dart.dataset.fetch_sources

dataset-dart:
	$(MAKE) dataset-dart-tools
	$(MAKE) dataset-dart-sources
	$(MAKE) dataset-dart-curriculum
	$(MAKE) dataset-dart-collect
	$(MAKE) dataset-dart-label
	$(MAKE) dataset-dart-validate
	$(MAKE) dataset-dart-prepare

dataset-dart-curriculum:
	$(PYTHON) -m packs.dart.dataset.generate_curriculum
	$(PYTHON) -m packs.dart.dataset.generate_literals
	$(PYTHON) -m packs.dart.dataset.generate_literals

dataset-dart-collect:
	$(PYTHON) -m packs.dart.dataset.pipeline collect

dataset-dart-label:
	$(PYTHON) -m packs.dart.dataset.pipeline label

dataset-dart-validate:
	$(PYTHON) -m packs.dart.dataset.pipeline validate

dataset-dart-prepare:
	$(PYTHON) -m training.dart.prepare

test-labeling-dart:
	$(PYTHON) -m unittest discover -s packs/dart/tests -v

train-dart-smoke:
	$(PYTHON) -m training.dart.train --smoke --epochs 1 --device $(DART_DEVICE) $(if $(DART_RUN),--output-dir "$(DART_RUN)") $(if $(DART_INIT_FROM),--init-from "$(DART_INIT_FROM)")

train-dart:
	$(PYTHON) -m training.dart.train --epochs $(DART_EPOCHS) --device $(DART_DEVICE) --batch-size $(DART_BATCH_SIZE) $(if $(DART_LEARNING_RATE),--learning-rate $(DART_LEARNING_RATE)) $(if $(DART_RUN),--output-dir "$(DART_RUN)") $(if $(DART_INIT_FROM),--init-from "$(DART_INIT_FROM)")

continue-dart:
	@test -n "$(DART_CHECKPOINT)" || (echo 'Set DART_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.dart.train --resume "$(DART_CHECKPOINT)" --epochs $(DART_EPOCHS) --device $(DART_DEVICE)

predict-dart:
	@test -n "$(DART_SOURCE)" || (echo 'Set DART_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.dart.predict --device $(DART_DEVICE) --file "$(DART_SOURCE)" $(if $(DART_CHECKPOINT),--checkpoint "$(DART_CHECKPOINT)")

evaluate-dart:
	@test -n "$(DART_CHECKPOINT)" || (echo 'Set DART_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.dart.evaluate --checkpoint "$(DART_CHECKPOINT)" --device $(DART_DEVICE) --split $(DART_EVAL_SPLIT)

challenge-dart:
	@test -n "$(DART_CHECKPOINT)" || (echo 'Set DART_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.dart.challenge --checkpoint "$(DART_CHECKPOINT)" --device $(DART_DEVICE)

export-dart-model:
	@test -n "$(DART_CHECKPOINT)" -a -n "$(DART_TEST_REPORT)" || (echo 'Set DART_CHECKPOINT and DART_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.dart.export_model --checkpoint "$(DART_CHECKPOINT)" --test-report "$(DART_TEST_REPORT)"

# Flutter application review reuses Dart weights; no new language model or SDK.
FLUTTER_REPORT ?= artifacts/flutter/real-apps-review.json
FLUTTER_CHALLENGE_REPORT ?= artifacts/flutter/challenges-review.json
.PHONY: dataset-flutter-examples evaluate-flutter challenge-flutter

dataset-flutter-examples:
	$(PYTHON) -m packs.dart.dataset.fetch_flutter_examples

evaluate-flutter:
	$(PYTHON) -m training.dart.evaluate_flutter --device $(DART_DEVICE) --output "$(FLUTTER_REPORT)"

challenge-flutter:
	$(PYTHON) -m training.dart.challenge_flutter --device $(DART_DEVICE) --output "$(FLUTTER_CHALLENGE_REPORT)"

SWIFT_DEVICE ?= auto
SWIFT_EPOCHS ?= 3
SWIFT_BATCH_SIZE ?= 32
SWIFT_LEARNING_RATE ?=
SWIFT_EVAL_SPLIT ?= validation

.PHONY: dataset-swift dataset-swift-tools dataset-swift-sources dataset-swift-curriculum dataset-swift-collect dataset-swift-label dataset-swift-validate dataset-swift-prepare test-labeling-swift train-swift-smoke train-swift continue-swift predict-swift evaluate-swift challenge-swift export-swift-model

dataset-swift-tools:
	$(PYTHON) -m packs.swift.labeling.tools

dataset-swift-sources:
	$(PYTHON) -m packs.swift.dataset.fetch_sources

dataset-swift:
	$(MAKE) dataset-swift-tools
	$(MAKE) dataset-swift-sources
	$(MAKE) dataset-swift-curriculum
	$(MAKE) dataset-swift-collect
	$(MAKE) dataset-swift-label
	$(MAKE) dataset-swift-validate
	$(MAKE) dataset-swift-prepare

dataset-swift-curriculum:
	$(PYTHON) -m packs.swift.dataset.generate_curriculum
	$(PYTHON) -m packs.swift.dataset.generate_literals

dataset-swift-collect:
	$(PYTHON) -m packs.swift.dataset.pipeline collect

dataset-swift-label:
	$(PYTHON) -m packs.swift.dataset.pipeline label

dataset-swift-validate:
	$(PYTHON) -m packs.swift.dataset.pipeline validate

dataset-swift-prepare:
	$(PYTHON) -m training.swift.prepare

test-labeling-swift:
	$(PYTHON) -m unittest discover -s packs/swift/tests -v

train-swift-smoke:
	$(PYTHON) -m training.swift.train --smoke --epochs 1 --device $(SWIFT_DEVICE) $(if $(SWIFT_RUN),--output-dir "$(SWIFT_RUN)") $(if $(SWIFT_INIT_FROM),--init-from "$(SWIFT_INIT_FROM)")

train-swift:
	$(PYTHON) -m training.swift.train --epochs $(SWIFT_EPOCHS) --device $(SWIFT_DEVICE) --batch-size $(SWIFT_BATCH_SIZE) $(if $(SWIFT_LEARNING_RATE),--learning-rate $(SWIFT_LEARNING_RATE)) $(if $(SWIFT_RUN),--output-dir "$(SWIFT_RUN)") $(if $(SWIFT_INIT_FROM),--init-from "$(SWIFT_INIT_FROM)")

continue-swift:
	@test -n "$(SWIFT_CHECKPOINT)" || (echo 'Set SWIFT_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.swift.train --resume "$(SWIFT_CHECKPOINT)" --epochs $(SWIFT_EPOCHS) --device $(SWIFT_DEVICE)

predict-swift:
	@test -n "$(SWIFT_SOURCE)" || (echo 'Set SWIFT_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.swift.predict --device $(SWIFT_DEVICE) --file "$(SWIFT_SOURCE)" $(if $(SWIFT_CHECKPOINT),--checkpoint "$(SWIFT_CHECKPOINT)")

evaluate-swift:
	@test -n "$(SWIFT_CHECKPOINT)" || (echo 'Set SWIFT_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.swift.evaluate --checkpoint "$(SWIFT_CHECKPOINT)" --device $(SWIFT_DEVICE) --split $(SWIFT_EVAL_SPLIT)

challenge-swift:
	@test -n "$(SWIFT_CHECKPOINT)" || (echo 'Set SWIFT_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.swift.challenge --checkpoint "$(SWIFT_CHECKPOINT)" --device $(SWIFT_DEVICE)

export-swift-model:
	@test -n "$(SWIFT_CHECKPOINT)" -a -n "$(SWIFT_TEST_REPORT)" || (echo 'Set SWIFT_CHECKPOINT and SWIFT_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.swift.export_model --checkpoint "$(SWIFT_CHECKPOINT)" --test-report "$(SWIFT_TEST_REPORT)"

KOTLIN_DEVICE ?= auto
KOTLIN_EPOCHS ?= 3
KOTLIN_BATCH_SIZE ?= 32
KOTLIN_LEARNING_RATE ?=
KOTLIN_EVAL_SPLIT ?= validation

.PHONY: dataset-kotlin dataset-kotlin-tools dataset-kotlin-sources dataset-kotlin-curriculum dataset-kotlin-collect dataset-kotlin-label dataset-kotlin-validate dataset-kotlin-prepare test-labeling-kotlin train-kotlin-smoke train-kotlin continue-kotlin predict-kotlin evaluate-kotlin challenge-kotlin export-kotlin-model

dataset-kotlin-tools:
	$(PYTHON) -m packs.kotlin.labeling.tools

dataset-kotlin-sources:
	$(PYTHON) -m packs.kotlin.dataset.fetch_sources

dataset-kotlin:
	$(MAKE) dataset-kotlin-tools
	$(MAKE) dataset-kotlin-sources
	$(MAKE) dataset-kotlin-curriculum
	$(MAKE) dataset-kotlin-collect
	$(MAKE) dataset-kotlin-label
	$(MAKE) dataset-kotlin-validate
	$(MAKE) dataset-kotlin-prepare

dataset-kotlin-curriculum:
	$(PYTHON) -m packs.kotlin.dataset.generate_curriculum
	$(PYTHON) -m packs.kotlin.dataset.generate_mixed

dataset-kotlin-collect:
	$(PYTHON) -m packs.kotlin.dataset.pipeline collect

dataset-kotlin-label:
	$(PYTHON) -m packs.kotlin.dataset.pipeline label

dataset-kotlin-validate:
	$(PYTHON) -m packs.kotlin.dataset.pipeline validate

dataset-kotlin-prepare:
	$(PYTHON) -m training.kotlin.prepare

test-labeling-kotlin:
	$(PYTHON) -m unittest discover -s packs/kotlin/tests -v

train-kotlin-smoke:
	$(PYTHON) -m training.kotlin.train --smoke --epochs 1 --device $(KOTLIN_DEVICE) $(if $(KOTLIN_RUN),--output-dir "$(KOTLIN_RUN)") $(if $(KOTLIN_INIT_FROM),--init-from "$(KOTLIN_INIT_FROM)")

train-kotlin:
	$(PYTHON) -m training.kotlin.train --epochs $(KOTLIN_EPOCHS) --device $(KOTLIN_DEVICE) --batch-size $(KOTLIN_BATCH_SIZE) $(if $(KOTLIN_LEARNING_RATE),--learning-rate $(KOTLIN_LEARNING_RATE)) $(if $(KOTLIN_RUN),--output-dir "$(KOTLIN_RUN)") $(if $(KOTLIN_INIT_FROM),--init-from "$(KOTLIN_INIT_FROM)")

continue-kotlin:
	@test -n "$(KOTLIN_CHECKPOINT)" || (echo 'Set KOTLIN_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.kotlin.train --resume "$(KOTLIN_CHECKPOINT)" --epochs $(KOTLIN_EPOCHS) --device $(KOTLIN_DEVICE)

predict-kotlin:
	@test -n "$(KOTLIN_SOURCE)" || (echo 'Set KOTLIN_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.kotlin.predict --device $(KOTLIN_DEVICE) --file "$(KOTLIN_SOURCE)" $(if $(KOTLIN_CHECKPOINT),--checkpoint "$(KOTLIN_CHECKPOINT)")

evaluate-kotlin:
	@test -n "$(KOTLIN_CHECKPOINT)" || (echo 'Set KOTLIN_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.kotlin.evaluate --checkpoint "$(KOTLIN_CHECKPOINT)" --device $(KOTLIN_DEVICE) --split $(KOTLIN_EVAL_SPLIT)

challenge-kotlin:
	@test -n "$(KOTLIN_CHECKPOINT)" || (echo 'Set KOTLIN_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.kotlin.challenge --checkpoint "$(KOTLIN_CHECKPOINT)" --device $(KOTLIN_DEVICE)

export-kotlin-model:
	@test -n "$(KOTLIN_CHECKPOINT)" -a -n "$(KOTLIN_TEST_REPORT)" || (echo 'Set KOTLIN_CHECKPOINT and KOTLIN_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.kotlin.export_model --checkpoint "$(KOTLIN_CHECKPOINT)" --test-report "$(KOTLIN_TEST_REPORT)"

R_DEVICE ?= auto
R_EPOCHS ?= 3
R_BATCH_SIZE ?= 32
R_LEARNING_RATE ?=
R_EVAL_SPLIT ?= validation

.PHONY: dataset-r dataset-r-tools dataset-r-sources dataset-r-curriculum dataset-r-collect dataset-r-label dataset-r-validate dataset-r-prepare test-labeling-r train-r-smoke train-r continue-r predict-r evaluate-r challenge-r export-r-model

dataset-r-tools:
	$(PYTHON) -m packs.r.labeling.tools

dataset-r-sources:
	$(PYTHON) -m packs.r.dataset.fetch_sources

dataset-r:
	$(MAKE) dataset-r-tools
	$(MAKE) dataset-r-sources
	$(MAKE) dataset-r-curriculum
	$(MAKE) dataset-r-collect
	$(MAKE) dataset-r-label
	$(MAKE) dataset-r-validate
	$(MAKE) dataset-r-prepare

dataset-r-curriculum:
	$(PYTHON) -m packs.r.dataset.generate_curriculum

dataset-r-collect:
	$(PYTHON) -m packs.r.dataset.pipeline collect

dataset-r-label:
	$(PYTHON) -m packs.r.dataset.pipeline label

dataset-r-validate:
	$(PYTHON) -m packs.r.dataset.pipeline validate

dataset-r-prepare:
	$(PYTHON) -m training.r.prepare

test-labeling-r:
	$(PYTHON) -m unittest discover -s packs/r/tests -v

train-r-smoke:
	$(PYTHON) -m training.r.train --smoke --epochs 1 --device $(R_DEVICE) $(if $(R_RUN),--output-dir "$(R_RUN)") $(if $(R_INIT_FROM),--init-from "$(R_INIT_FROM)")

train-r:
	$(PYTHON) -m training.r.train --epochs $(R_EPOCHS) --device $(R_DEVICE) --batch-size $(R_BATCH_SIZE) $(if $(R_LEARNING_RATE),--learning-rate $(R_LEARNING_RATE)) $(if $(R_RUN),--output-dir "$(R_RUN)") $(if $(R_INIT_FROM),--init-from "$(R_INIT_FROM)")

continue-r:
	@test -n "$(R_CHECKPOINT)" || (echo 'Set R_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.r.train --resume "$(R_CHECKPOINT)" --epochs $(R_EPOCHS) --device $(R_DEVICE)

predict-r:
	@test -n "$(R_SOURCE)" || (echo 'Set R_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.r.predict --device $(R_DEVICE) --file "$(R_SOURCE)" $(if $(R_CHECKPOINT),--checkpoint "$(R_CHECKPOINT)")

evaluate-r:
	@test -n "$(R_CHECKPOINT)" || (echo 'Set R_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.r.evaluate --checkpoint "$(R_CHECKPOINT)" --device $(R_DEVICE) --split $(R_EVAL_SPLIT)

challenge-r:
	@test -n "$(R_CHECKPOINT)" || (echo 'Set R_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.r.challenge --checkpoint "$(R_CHECKPOINT)" --device $(R_DEVICE)

export-r-model:
	@test -n "$(R_CHECKPOINT)" -a -n "$(R_TEST_REPORT)" || (echo 'Set R_CHECKPOINT and R_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.r.export_model --checkpoint "$(R_CHECKPOINT)" --test-report "$(R_TEST_REPORT)"

SCALA_DEVICE ?= auto
SCALA_EPOCHS ?= 3
SCALA_BATCH_SIZE ?= 32
SCALA_LEARNING_RATE ?=
SCALA_EVAL_SPLIT ?= validation

.PHONY: dataset-scala dataset-scala-tools dataset-scala-sources dataset-scala-curriculum dataset-scala-collect dataset-scala-label dataset-scala-validate dataset-scala-prepare test-labeling-scala train-scala-smoke train-scala continue-scala predict-scala evaluate-scala challenge-scala export-scala-model

dataset-scala-tools:
	$(PYTHON) -m packs.scala.labeling.tools

dataset-scala-sources:
	$(PYTHON) -m packs.scala.dataset.fetch_sources

dataset-scala:
	$(MAKE) dataset-scala-tools
	$(MAKE) dataset-scala-sources
	$(MAKE) dataset-scala-curriculum
	$(MAKE) dataset-scala-collect
	$(MAKE) dataset-scala-label
	$(MAKE) dataset-scala-validate
	$(MAKE) dataset-scala-prepare

dataset-scala-curriculum:
	$(PYTHON) -m packs.scala.dataset.generate_curriculum

dataset-scala-collect:
	$(PYTHON) -m packs.scala.dataset.pipeline collect

dataset-scala-label:
	$(PYTHON) -m packs.scala.dataset.pipeline label

dataset-scala-validate:
	$(PYTHON) -m packs.scala.dataset.pipeline validate

dataset-scala-prepare:
	$(PYTHON) -m training.scala.prepare

test-labeling-scala:
	$(PYTHON) -m unittest discover -s packs/scala/tests -v

train-scala-smoke:
	$(PYTHON) -m training.scala.train --smoke --epochs 1 --device $(SCALA_DEVICE) $(if $(SCALA_RUN),--output-dir "$(SCALA_RUN)") $(if $(SCALA_INIT_FROM),--init-from "$(SCALA_INIT_FROM)")

train-scala:
	$(PYTHON) -m training.scala.train --epochs $(SCALA_EPOCHS) --device $(SCALA_DEVICE) --batch-size $(SCALA_BATCH_SIZE) $(if $(SCALA_LEARNING_RATE),--learning-rate $(SCALA_LEARNING_RATE)) $(if $(SCALA_RUN),--output-dir "$(SCALA_RUN)") $(if $(SCALA_INIT_FROM),--init-from "$(SCALA_INIT_FROM)")

continue-scala:
	@test -n "$(SCALA_CHECKPOINT)" || (echo 'Set SCALA_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.scala.train --resume "$(SCALA_CHECKPOINT)" --epochs $(SCALA_EPOCHS) --device $(SCALA_DEVICE)

predict-scala:
	@test -n "$(SCALA_SOURCE)" || (echo 'Set SCALA_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.scala.predict --device $(SCALA_DEVICE) --file "$(SCALA_SOURCE)" $(if $(SCALA_CHECKPOINT),--checkpoint "$(SCALA_CHECKPOINT)")

evaluate-scala:
	@test -n "$(SCALA_CHECKPOINT)" || (echo 'Set SCALA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.scala.evaluate --checkpoint "$(SCALA_CHECKPOINT)" --device $(SCALA_DEVICE) --split $(SCALA_EVAL_SPLIT)

challenge-scala:
	@test -n "$(SCALA_CHECKPOINT)" || (echo 'Set SCALA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.scala.challenge --checkpoint "$(SCALA_CHECKPOINT)" --device $(SCALA_DEVICE)

export-scala-model:
	@test -n "$(SCALA_CHECKPOINT)" -a -n "$(SCALA_TEST_REPORT)" || (echo 'Set SCALA_CHECKPOINT and SCALA_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.scala.export_model --checkpoint "$(SCALA_CHECKPOINT)" --test-report "$(SCALA_TEST_REPORT)"

RUBY_DEVICE ?= auto
RUBY_EPOCHS ?= 3
RUBY_BATCH_SIZE ?= 32
RUBY_LEARNING_RATE ?=
RUBY_EVAL_SPLIT ?= validation

.PHONY: dataset-ruby dataset-ruby-tools dataset-ruby-sources dataset-ruby-curriculum dataset-ruby-collect dataset-ruby-label dataset-ruby-validate dataset-ruby-prepare test-labeling-ruby train-ruby-smoke train-ruby continue-ruby predict-ruby evaluate-ruby challenge-ruby export-ruby-model

dataset-ruby-tools:
	$(PYTHON) -m packs.ruby.labeling.tools

dataset-ruby-sources:
	$(PYTHON) -m packs.ruby.dataset.fetch_sources

dataset-ruby:
	$(MAKE) dataset-ruby-tools
	$(MAKE) dataset-ruby-sources
	$(MAKE) dataset-ruby-curriculum
	$(MAKE) dataset-ruby-collect
	$(MAKE) dataset-ruby-label
	$(MAKE) dataset-ruby-validate
	$(MAKE) dataset-ruby-prepare

dataset-ruby-curriculum:
	$(PYTHON) -m packs.ruby.dataset.generate_curriculum
	$(PYTHON) -m packs.ruby.dataset.generate_mixed

dataset-ruby-collect:
	$(PYTHON) -m packs.ruby.dataset.pipeline collect

dataset-ruby-label:
	$(PYTHON) -m packs.ruby.dataset.pipeline label

dataset-ruby-validate:
	$(PYTHON) -m packs.ruby.dataset.pipeline validate

dataset-ruby-prepare:
	$(PYTHON) -m training.ruby.prepare

test-labeling-ruby:
	$(PYTHON) -m unittest discover -s packs/ruby/tests -v

train-ruby-smoke:
	$(PYTHON) -m training.ruby.train --smoke --epochs 1 --device $(RUBY_DEVICE) $(if $(RUBY_RUN),--output-dir "$(RUBY_RUN)") $(if $(RUBY_INIT_FROM),--init-from "$(RUBY_INIT_FROM)")

train-ruby:
	$(PYTHON) -m training.ruby.train --epochs $(RUBY_EPOCHS) --device $(RUBY_DEVICE) --batch-size $(RUBY_BATCH_SIZE) $(if $(RUBY_LEARNING_RATE),--learning-rate $(RUBY_LEARNING_RATE)) $(if $(RUBY_RUN),--output-dir "$(RUBY_RUN)") $(if $(RUBY_INIT_FROM),--init-from "$(RUBY_INIT_FROM)")

continue-ruby:
	@test -n "$(RUBY_CHECKPOINT)" || (echo 'Set RUBY_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.ruby.train --resume "$(RUBY_CHECKPOINT)" --epochs $(RUBY_EPOCHS) --device $(RUBY_DEVICE)

predict-ruby:
	@test -n "$(RUBY_SOURCE)" || (echo 'Set RUBY_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.ruby.predict --device $(RUBY_DEVICE) --file "$(RUBY_SOURCE)" $(if $(RUBY_CHECKPOINT),--checkpoint "$(RUBY_CHECKPOINT)")

evaluate-ruby:
	@test -n "$(RUBY_CHECKPOINT)" || (echo 'Set RUBY_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.ruby.evaluate --checkpoint "$(RUBY_CHECKPOINT)" --device $(RUBY_DEVICE) --split $(RUBY_EVAL_SPLIT)

challenge-ruby:
	@test -n "$(RUBY_CHECKPOINT)" || (echo 'Set RUBY_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.ruby.challenge --checkpoint "$(RUBY_CHECKPOINT)" --device $(RUBY_DEVICE)

export-ruby-model:
	@test -n "$(RUBY_CHECKPOINT)" -a -n "$(RUBY_TEST_REPORT)" || (echo 'Set RUBY_CHECKPOINT and RUBY_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.ruby.export_model --checkpoint "$(RUBY_CHECKPOINT)" --test-report "$(RUBY_TEST_REPORT)"

LUA_DEVICE ?= auto
LUA_EPOCHS ?= 3
LUA_BATCH_SIZE ?= 32
LUA_LEARNING_RATE ?=
LUA_EVAL_SPLIT ?= validation

.PHONY: dataset-lua dataset-lua-tools dataset-lua-sources dataset-lua-curriculum dataset-lua-collect dataset-lua-label dataset-lua-validate dataset-lua-prepare test-labeling-lua train-lua-smoke train-lua continue-lua predict-lua evaluate-lua challenge-lua export-lua-model

dataset-lua-tools:
	$(PYTHON) -m packs.lua.labeling.tools

dataset-lua-sources:
	$(PYTHON) -m packs.lua.dataset.fetch_sources

dataset-lua:
	$(MAKE) dataset-lua-tools
	$(MAKE) dataset-lua-sources
	$(MAKE) dataset-lua-curriculum
	$(MAKE) dataset-lua-collect
	$(MAKE) dataset-lua-label
	$(MAKE) dataset-lua-validate
	$(MAKE) dataset-lua-prepare

dataset-lua-curriculum:
	$(PYTHON) -m packs.lua.dataset.generate_curriculum

dataset-lua-collect:
	$(PYTHON) -m packs.lua.dataset.pipeline collect

dataset-lua-label:
	$(PYTHON) -m packs.lua.dataset.pipeline label

dataset-lua-validate:
	$(PYTHON) -m packs.lua.dataset.pipeline validate

dataset-lua-prepare:
	$(PYTHON) -m training.lua.prepare

test-labeling-lua:
	$(PYTHON) -m unittest discover -s packs/lua/tests -v

train-lua-smoke:
	$(PYTHON) -m training.lua.train --smoke --epochs 1 --device $(LUA_DEVICE) $(if $(LUA_RUN),--output-dir "$(LUA_RUN)") $(if $(LUA_INIT_FROM),--init-from "$(LUA_INIT_FROM)")

train-lua:
	$(PYTHON) -m training.lua.train --epochs $(LUA_EPOCHS) --device $(LUA_DEVICE) --batch-size $(LUA_BATCH_SIZE) $(if $(LUA_LEARNING_RATE),--learning-rate $(LUA_LEARNING_RATE)) $(if $(LUA_RUN),--output-dir "$(LUA_RUN)") $(if $(LUA_INIT_FROM),--init-from "$(LUA_INIT_FROM)")

continue-lua:
	@test -n "$(LUA_CHECKPOINT)" || (echo 'Set LUA_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.lua.train --resume "$(LUA_CHECKPOINT)" --epochs $(LUA_EPOCHS) --device $(LUA_DEVICE)

predict-lua:
	@test -n "$(LUA_SOURCE)" || (echo 'Set LUA_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.lua.predict --device $(LUA_DEVICE) --file "$(LUA_SOURCE)" $(if $(LUA_CHECKPOINT),--checkpoint "$(LUA_CHECKPOINT)")

evaluate-lua:
	@test -n "$(LUA_CHECKPOINT)" || (echo 'Set LUA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.lua.evaluate --checkpoint "$(LUA_CHECKPOINT)" --device $(LUA_DEVICE) --split $(LUA_EVAL_SPLIT)

challenge-lua:
	@test -n "$(LUA_CHECKPOINT)" || (echo 'Set LUA_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.lua.challenge --checkpoint "$(LUA_CHECKPOINT)" --device $(LUA_DEVICE)

export-lua-model:
	@test -n "$(LUA_CHECKPOINT)" -a -n "$(LUA_TEST_REPORT)" || (echo 'Set LUA_CHECKPOINT and LUA_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.lua.export_model --checkpoint "$(LUA_CHECKPOINT)" --test-report "$(LUA_TEST_REPORT)"

JSON_DEVICE ?= auto
JSON_EPOCHS ?= 3
JSON_BATCH_SIZE ?= 32
JSON_LEARNING_RATE ?=
JSON_EVAL_SPLIT ?= validation

.PHONY: dataset-json dataset-json-tools dataset-json-sources dataset-json-curriculum dataset-json-collect dataset-json-label dataset-json-validate dataset-json-prepare test-labeling-json train-json-smoke train-json continue-json predict-json evaluate-json challenge-json export-json-model

dataset-json-tools:
	$(PYTHON) -m packs.json.labeling.tools

dataset-json-sources:
	$(PYTHON) -m packs.json.dataset.fetch_sources

dataset-json:
	$(MAKE) dataset-json-tools
	$(MAKE) dataset-json-sources
	$(MAKE) dataset-json-curriculum
	$(MAKE) dataset-json-collect
	$(MAKE) dataset-json-label
	$(MAKE) dataset-json-validate
	$(MAKE) dataset-json-prepare

dataset-json-curriculum:
	$(PYTHON) -m packs.json.dataset.generate_curriculum
	$(PYTHON) -m packs.json.dataset.generate_mixed

dataset-json-collect:
	$(PYTHON) -m packs.json.dataset.pipeline collect

dataset-json-label:
	$(PYTHON) -m packs.json.dataset.pipeline label

dataset-json-validate:
	$(PYTHON) -m packs.json.dataset.pipeline validate

dataset-json-prepare:
	$(PYTHON) -m training.json.prepare

test-labeling-json:
	$(PYTHON) -m unittest discover -s packs/json/tests -v

train-json-smoke:
	$(PYTHON) -m training.json.train --smoke --epochs 1 --device $(JSON_DEVICE) $(if $(JSON_RUN),--output-dir "$(JSON_RUN)") $(if $(JSON_INIT_FROM),--init-from "$(JSON_INIT_FROM)")

train-json:
	$(PYTHON) -m training.json.train --epochs $(JSON_EPOCHS) --device $(JSON_DEVICE) --batch-size $(JSON_BATCH_SIZE) $(if $(JSON_LEARNING_RATE),--learning-rate $(JSON_LEARNING_RATE)) $(if $(JSON_RUN),--output-dir "$(JSON_RUN)") $(if $(JSON_INIT_FROM),--init-from "$(JSON_INIT_FROM)")

continue-json:
	@test -n "$(JSON_CHECKPOINT)" || (echo 'Set JSON_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.json.train --resume "$(JSON_CHECKPOINT)" --epochs $(JSON_EPOCHS) --device $(JSON_DEVICE)

predict-json:
	@test -n "$(JSON_SOURCE)" || (echo 'Set JSON_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.json.predict --device $(JSON_DEVICE) --file "$(JSON_SOURCE)" $(if $(JSON_CHECKPOINT),--checkpoint "$(JSON_CHECKPOINT)")

evaluate-json:
	@test -n "$(JSON_CHECKPOINT)" || (echo 'Set JSON_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.json.evaluate --checkpoint "$(JSON_CHECKPOINT)" --device $(JSON_DEVICE) --split $(JSON_EVAL_SPLIT)

challenge-json:
	@test -n "$(JSON_CHECKPOINT)" || (echo 'Set JSON_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.json.challenge --checkpoint "$(JSON_CHECKPOINT)" --device $(JSON_DEVICE)

export-json-model:
	@test -n "$(JSON_CHECKPOINT)" -a -n "$(JSON_TEST_REPORT)" || (echo 'Set JSON_CHECKPOINT and JSON_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.json.export_model --checkpoint "$(JSON_CHECKPOINT)" --test-report "$(JSON_TEST_REPORT)"

YAML_DEVICE ?= auto
YAML_EPOCHS ?= 3
YAML_BATCH_SIZE ?= 32
YAML_LEARNING_RATE ?=
YAML_EVAL_SPLIT ?= validation

.PHONY: dataset-yaml dataset-yaml-tools dataset-yaml-sources dataset-yaml-curriculum dataset-yaml-collect dataset-yaml-label dataset-yaml-validate dataset-yaml-prepare test-labeling-yaml train-yaml-smoke train-yaml continue-yaml predict-yaml evaluate-yaml challenge-yaml export-yaml-model

dataset-yaml-tools:
	$(PYTHON) -m packs.yaml.labeling.tools

dataset-yaml-sources:
	$(PYTHON) -m packs.yaml.dataset.fetch_sources

dataset-yaml:
	$(MAKE) dataset-yaml-tools
	$(MAKE) dataset-yaml-sources
	$(MAKE) dataset-yaml-curriculum
	$(MAKE) dataset-yaml-collect
	$(MAKE) dataset-yaml-label
	$(MAKE) dataset-yaml-validate
	$(MAKE) dataset-yaml-prepare

dataset-yaml-curriculum:
	$(PYTHON) -m packs.yaml.dataset.generate_curriculum
	$(PYTHON) -m packs.yaml.dataset.generate_mixed

dataset-yaml-collect:
	$(PYTHON) -m packs.yaml.dataset.pipeline collect

dataset-yaml-label:
	$(PYTHON) -m packs.yaml.dataset.pipeline label

dataset-yaml-validate:
	$(PYTHON) -m packs.yaml.dataset.pipeline validate

dataset-yaml-prepare:
	$(PYTHON) -m training.yaml.prepare

test-labeling-yaml:
	$(PYTHON) -m unittest discover -s packs/yaml/tests -v

train-yaml-smoke:
	$(PYTHON) -m training.yaml.train --smoke --epochs 1 --device $(YAML_DEVICE) $(if $(YAML_RUN),--output-dir "$(YAML_RUN)") $(if $(YAML_INIT_FROM),--init-from "$(YAML_INIT_FROM)")

train-yaml:
	$(PYTHON) -m training.yaml.train --epochs $(YAML_EPOCHS) --device $(YAML_DEVICE) --batch-size $(YAML_BATCH_SIZE) $(if $(YAML_LEARNING_RATE),--learning-rate $(YAML_LEARNING_RATE)) $(if $(YAML_RUN),--output-dir "$(YAML_RUN)") $(if $(YAML_INIT_FROM),--init-from "$(YAML_INIT_FROM)")

continue-yaml:
	@test -n "$(YAML_CHECKPOINT)" || (echo 'Set YAML_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.yaml.train --resume "$(YAML_CHECKPOINT)" --epochs $(YAML_EPOCHS) --device $(YAML_DEVICE)

predict-yaml:
	@test -n "$(YAML_SOURCE)" || (echo 'Set YAML_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.yaml.predict --device $(YAML_DEVICE) --file "$(YAML_SOURCE)" $(if $(YAML_CHECKPOINT),--checkpoint "$(YAML_CHECKPOINT)")

evaluate-yaml:
	@test -n "$(YAML_CHECKPOINT)" || (echo 'Set YAML_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.yaml.evaluate --checkpoint "$(YAML_CHECKPOINT)" --device $(YAML_DEVICE) --split $(YAML_EVAL_SPLIT)

challenge-yaml:
	@test -n "$(YAML_CHECKPOINT)" || (echo 'Set YAML_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.yaml.challenge --checkpoint "$(YAML_CHECKPOINT)" --device $(YAML_DEVICE)

export-yaml-model:
	@test -n "$(YAML_CHECKPOINT)" -a -n "$(YAML_TEST_REPORT)" || (echo 'Set YAML_CHECKPOINT and YAML_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.yaml.export_model --checkpoint "$(YAML_CHECKPOINT)" --test-report "$(YAML_TEST_REPORT)"

TOML_DEVICE ?= auto
TOML_EPOCHS ?= 3
TOML_BATCH_SIZE ?= 32
TOML_LEARNING_RATE ?=
TOML_EVAL_SPLIT ?= validation

.PHONY: dataset-toml dataset-toml-tools dataset-toml-sources dataset-toml-curriculum dataset-toml-collect dataset-toml-label dataset-toml-validate dataset-toml-prepare test-labeling-toml train-toml-smoke train-toml continue-toml predict-toml evaluate-toml challenge-toml export-toml-model

dataset-toml-tools:
	$(PYTHON) -m packs.toml.labeling.tools

dataset-toml-sources:
	$(PYTHON) -m packs.toml.dataset.fetch_sources

dataset-toml:
	$(MAKE) dataset-toml-tools
	$(MAKE) dataset-toml-sources
	$(MAKE) dataset-toml-curriculum
	$(MAKE) dataset-toml-collect
	$(MAKE) dataset-toml-label
	$(MAKE) dataset-toml-validate
	$(MAKE) dataset-toml-prepare

dataset-toml-curriculum:
	$(PYTHON) -m packs.toml.dataset.generate_curriculum
	$(PYTHON) -m packs.toml.dataset.generate_mixed

dataset-toml-collect:
	$(PYTHON) -m packs.toml.dataset.pipeline collect

dataset-toml-label:
	$(PYTHON) -m packs.toml.dataset.pipeline label

dataset-toml-validate:
	$(PYTHON) -m packs.toml.dataset.pipeline validate

dataset-toml-prepare:
	$(PYTHON) -m training.toml.prepare

test-labeling-toml:
	$(PYTHON) -m unittest discover -s packs/toml/tests -v

train-toml-smoke:
	$(PYTHON) -m training.toml.train --smoke --epochs 1 --device $(TOML_DEVICE) $(if $(TOML_RUN),--output-dir "$(TOML_RUN)") $(if $(TOML_INIT_FROM),--init-from "$(TOML_INIT_FROM)")

train-toml:
	$(PYTHON) -m training.toml.train --epochs $(TOML_EPOCHS) --device $(TOML_DEVICE) --batch-size $(TOML_BATCH_SIZE) $(if $(TOML_LEARNING_RATE),--learning-rate $(TOML_LEARNING_RATE)) $(if $(TOML_RUN),--output-dir "$(TOML_RUN)") $(if $(TOML_INIT_FROM),--init-from "$(TOML_INIT_FROM)")

continue-toml:
	@test -n "$(TOML_CHECKPOINT)" || (echo 'Set TOML_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.toml.train --resume "$(TOML_CHECKPOINT)" --epochs $(TOML_EPOCHS) --device $(TOML_DEVICE)

predict-toml:
	@test -n "$(TOML_SOURCE)" || (echo 'Set TOML_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.toml.predict --device $(TOML_DEVICE) --file "$(TOML_SOURCE)" $(if $(TOML_CHECKPOINT),--checkpoint "$(TOML_CHECKPOINT)")

evaluate-toml:
	@test -n "$(TOML_CHECKPOINT)" || (echo 'Set TOML_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.toml.evaluate --checkpoint "$(TOML_CHECKPOINT)" --device $(TOML_DEVICE) --split $(TOML_EVAL_SPLIT)

challenge-toml:
	@test -n "$(TOML_CHECKPOINT)" || (echo 'Set TOML_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.toml.challenge --checkpoint "$(TOML_CHECKPOINT)" --device $(TOML_DEVICE)

export-toml-model:
	@test -n "$(TOML_CHECKPOINT)" -a -n "$(TOML_TEST_REPORT)" || (echo 'Set TOML_CHECKPOINT and TOML_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.toml.export_model --checkpoint "$(TOML_CHECKPOINT)" --test-report "$(TOML_TEST_REPORT)"

INI_DEVICE ?= auto
INI_EPOCHS ?= 3
INI_BATCH_SIZE ?= 32
INI_LEARNING_RATE ?=
INI_EVAL_SPLIT ?= validation

.PHONY: dataset-ini dataset-ini-tools dataset-ini-sources dataset-ini-curriculum dataset-ini-collect dataset-ini-label dataset-ini-validate dataset-ini-prepare test-labeling-ini train-ini-smoke train-ini continue-ini predict-ini evaluate-ini challenge-ini export-ini-model

dataset-ini-tools:
	$(PYTHON) -m packs.ini.labeling.tools

dataset-ini-sources:
	$(PYTHON) -m packs.ini.dataset.fetch_sources

dataset-ini:
	$(MAKE) dataset-ini-tools
	$(MAKE) dataset-ini-sources
	$(MAKE) dataset-ini-curriculum
	$(MAKE) dataset-ini-collect
	$(MAKE) dataset-ini-label
	$(MAKE) dataset-ini-validate
	$(MAKE) dataset-ini-prepare

dataset-ini-curriculum:
	$(PYTHON) -m packs.ini.dataset.generate_curriculum

dataset-ini-collect:
	$(PYTHON) -m packs.ini.dataset.pipeline collect

dataset-ini-label:
	$(PYTHON) -m packs.ini.dataset.pipeline label

dataset-ini-validate:
	$(PYTHON) -m packs.ini.dataset.pipeline validate

dataset-ini-prepare:
	$(PYTHON) -m training.ini.prepare

test-labeling-ini:
	$(PYTHON) -m unittest discover -s packs/ini/tests -v

train-ini-smoke:
	$(PYTHON) -m training.ini.train --smoke --epochs 1 --device $(INI_DEVICE) $(if $(INI_RUN),--output-dir "$(INI_RUN)") $(if $(INI_INIT_FROM),--init-from "$(INI_INIT_FROM)")

train-ini:
	$(PYTHON) -m training.ini.train --epochs $(INI_EPOCHS) --device $(INI_DEVICE) --batch-size $(INI_BATCH_SIZE) $(if $(INI_LEARNING_RATE),--learning-rate $(INI_LEARNING_RATE)) $(if $(INI_RUN),--output-dir "$(INI_RUN)") $(if $(INI_INIT_FROM),--init-from "$(INI_INIT_FROM)")

continue-ini:
	@test -n "$(INI_CHECKPOINT)" || (echo 'Set INI_CHECKPOINT to the run last.pt'; exit 1)
	$(PYTHON) -m training.ini.train --resume "$(INI_CHECKPOINT)" --epochs $(INI_EPOCHS) --device $(INI_DEVICE)

predict-ini:
	@test -n "$(INI_SOURCE)" || (echo 'Set INI_SOURCE to a source file'; exit 1)
	$(PYTHON) -m training.ini.predict --device $(INI_DEVICE) --file "$(INI_SOURCE)" $(if $(INI_CHECKPOINT),--checkpoint "$(INI_CHECKPOINT)")

evaluate-ini:
	@test -n "$(INI_CHECKPOINT)" || (echo 'Set INI_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.ini.evaluate --checkpoint "$(INI_CHECKPOINT)" --device $(INI_DEVICE) --split $(INI_EVAL_SPLIT)

challenge-ini:
	@test -n "$(INI_CHECKPOINT)" || (echo 'Set INI_CHECKPOINT to a frozen candidate'; exit 1)
	$(PYTHON) -m training.ini.challenge --checkpoint "$(INI_CHECKPOINT)" --device $(INI_DEVICE)

export-ini-model:
	@test -n "$(INI_CHECKPOINT)" -a -n "$(INI_TEST_REPORT)" || (echo 'Set INI_CHECKPOINT and INI_TEST_REPORT'; exit 1)
	$(PYTHON) -m training.ini.export_model --checkpoint "$(INI_CHECKPOINT)" --test-report "$(INI_TEST_REPORT)"
