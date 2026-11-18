# Definition bodies stay original, opaque source.
define MESSAGE
Release notes for $(PROJECT).
# This line belongs to the definition value.
endef

PROJECT ?= preview

.PHONY: message
message:
	@printf '%s\n' "$(PROJECT)"
