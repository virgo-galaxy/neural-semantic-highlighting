# Build the original C sources.
CC ?= cc
CFLAGS ?= -O2 -Wall
SOURCES := $(wildcard src/*.c)
OBJECTS := $(SOURCES:src/%.c=build/%.o)

.PHONY: all clean
all: build/app

build/app: $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^

build/%.o: src/%.c | build
	$(CC) $(CFLAGS) -c $< -o $@

build:
	mkdir -p $@

clean:
	rm -rf build
