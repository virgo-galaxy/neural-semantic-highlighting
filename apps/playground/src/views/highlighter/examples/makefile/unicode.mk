# 保留原文、制表符与换行 🌌
TITLE = "你好 🌌"
.RECIPEPREFIX = >

.PHONY: greeting
greeting:
> @printf '%s\n' "$(TITLE)"
> @echo "$$HOME"
