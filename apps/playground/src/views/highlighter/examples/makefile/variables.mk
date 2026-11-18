# Assignment flavors and original variable references.
PROJECT = preview
PREFIX ?= /usr/local
OUTPUT := build/$(PROJECT)
FLAGS += -Wall
export PROJECT

SOURCES := $(wildcard src/*.c)
OBJECTS := $(patsubst src/%.c,$(OUTPUT)/%.o,$(SOURCES))

.PHONY: inspect
inspect:
	@printf '%s\n' "$(PROJECT) $(PREFIX)"
	@echo "Home: $$HOME"
