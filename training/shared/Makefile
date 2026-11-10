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
