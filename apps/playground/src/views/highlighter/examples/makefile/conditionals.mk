MODE ?= release
CC ?= cc

ifeq ($(MODE),debug)
FLAGS += -g -O0
else
FLAGS += -O2
endif

ifdef EXTRA_CHECKS
FLAGS += -Wextra
endif

-include local.mk
export MODE

.PHONY: show
show:
	@echo "$(MODE): $(FLAGS)"
