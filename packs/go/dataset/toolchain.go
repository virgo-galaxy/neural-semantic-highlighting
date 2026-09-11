package dataset

import (
	"fmt"
	"runtime"
)

func RequireGoldToolchain() error {
	if runtime.Version() != GoldToolchain {
		return fmt.Errorf(
			"Go dataset tooling requires %s, running %s",
			GoldToolchain,
			runtime.Version(),
		)
	}
	return nil
}
