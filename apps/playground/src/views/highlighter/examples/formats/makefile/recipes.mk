OUTPUT ?= output

.PHONY: prepare report clean
prepare:
	mkdir -p $(OUTPUT)

report: prepare
	@for name in alpha beta; do \
	  printf '%s\n' "$$name"; \
	done
	@echo "Original shell value: $$HOME"
	@echo "Make target: $@"

clean:
	-rm -rf $(OUTPUT)
