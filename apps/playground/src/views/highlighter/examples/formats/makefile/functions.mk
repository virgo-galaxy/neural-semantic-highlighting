SOURCES := $(wildcard source/*.c)
NAMES := $(notdir $(SOURCES))
OBJECTS := $(addprefix output/,$(NAMES:.c=.o))
SORTED := $(sort $(OBJECTS))
FIRST := $(firstword $(SORTED))

.PHONY: list
list:
	@printf '%s\n' "$(FIRST)"
	@echo "$(words $(SORTED)) objects"
