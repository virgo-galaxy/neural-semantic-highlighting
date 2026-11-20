CC ?= cc
OBJECTS = build/main.o build/util.o

.PHONY: all test clean
all: $(OBJECTS)

$(OBJECTS): | build

$(OBJECTS): build/%.o: src/%.c
	$(CC) -c $< -o $@

build:
	mkdir -p $@

test::
	@echo first check

test::
	@echo second check

clean: ; rm -rf build
