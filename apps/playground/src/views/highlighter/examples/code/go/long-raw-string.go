package docs

const Manual = `# Command reference

This intentionally long raw string crosses the model's 512-byte context boundary.
It is here to make the Playground expose the exact boundary case we discussed,
rather than hiding it behind aggregate metrics. The model receives source bytes
locally and must decide span boundaries without a Go scanner, parser, AST, type
checker, or compiler at runtime.

| Command | Description |
| --- | --- |
| serve | Start the local service and wait for connections. |
| check | Validate configuration before starting the process. |
| status | Print a short status summary for the current process. |
| stop | Stop the service after active work has finished. |
| reset | Restore the example configuration to its initial values. |

The remaining text simply keeps the raw string comfortably above five hundred
bytes so that the verification is visible in the real UI instead of inferred
from a synthetic score.`

func Help() string {
	return Manual
}
