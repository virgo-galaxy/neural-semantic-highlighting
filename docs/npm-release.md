# npm release preparation

This runbook prepares and verifies local release candidates. The GitHub
repository and the workspace packages are currently private. Candidate `.tgz`
files retain `private: true` and can be installed into a test project.

## Decisions for the first release

| Decision            | Confirm before preparing the final artifacts                                                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| npm namespace       | Confirm the publishing account controls the chosen scope and can complete npm's publishing authentication. The workspace currently uses `@nsh`.                                        |
| Distribution rights | Confirm the license for the project code and distribution rights for the model assets in scope. Include the approved license text and applicable third-party notices in the artifacts. |
| Model delivery      | Decide whether to include the optional model package in the first release. Remote apps also need access to independently hosted ONNX and JSON resources from the matching build.       |

The runtime packages are `@nsh/core`, `@nsh/html`, `@nsh/browser` and
`@nsh/highlighter`. Local bundling uses the optional `@nsh/models` package.
The themes ship through the highlighter. The Playground and Python tooling stay
in the workspace. See [model delivery](model-delivery.md) for the two modes.

## Build and verify a candidate

Use a fresh checkout of the candidate revision with Node.js 24 and the pnpm
version recorded in the lockfile. Keep the frozen lockfile check enabled so a
manifest change is visible before packaging.

```bash
pnpm install --frozen-lockfile
pnpm all
pnpm pack:browser
node scripts/check-model-delivery.mjs
```

`pnpm all` runs the workspace builds, type checking, lint, formatting, tests and
the portable-path check. `pnpm pack:browser` writes five local archives under
`artifacts/browser/npm/`. The packer resolves `workspace:` ranges to concrete
versions in the staged manifests. Building all five candidates exercises both
delivery modes while the scope of the first release is pending.

Review `artifacts/browser/npm/archives.json` and
`artifacts/browser/delivery-check/verification.json`. Confirm the following in
the candidate files and consumer builds:

- All `@nsh` runtime dependencies use matching versions. The direct install of
  the four base archives works with `@nsh/models` absent.
- The local TSX/SCSS build emits exactly two ONNX files with the expected model
  hashes. The remote build emits zero ONNX files. Each emits one shared WASM.
- Archives contain the expected runtime files and notices. ONNX weights belong
  in the model archive. Check for accidental training files, credentials and host paths.
- Serve `artifacts/browser/delivery-check/local/` and `remote/` each as its own
  site root, and confirm that both highlight source. For the remote example,
  configure `?models=<URL>` to point at the separately served
  [exported directory](model-delivery.md#export-the-deployable-directory).

To prepare the matching assets for that check, run this from the checkout:

```bash
node scripts/export-model-assets.mjs
```

Keep model and metadata paths together when serving the export. For public
remote delivery, verify the real resource URL from a consuming browser,
including CORS if the app and host are on different origins.

With an existing `reference.json`, pass `--reference <path>` to the consumer
check and open the remote example with `&reference=reference.json` to compare
browser output with the recorded reference.

## Final artifact review

After the three release decisions are made, apply the approved package names,
versions, licenses and access to the intended npm artifacts. Update the npm
README with registry installation commands and links usable by recipients.
Review the exact file list and hashes again after these changes.

The package dependency order is core, then html and browser, then highlighter.
If the optional model package is in scope, it depends on browser. Once the
approved release is available, test a registry install in a new consumer app.
