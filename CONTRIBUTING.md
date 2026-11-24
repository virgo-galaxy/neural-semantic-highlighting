# Contributing

Follow the [Code of Conduct](CODE_OF_CONDUCT.md) in project spaces.

## Ask questions or report a bug

Use [Discussions](https://github.com/virgo-galaxy/virgo-nsh/discussions) for usage
questions and proposals. Use [Issues](https://github.com/virgo-galaxy/virgo-nsh/issues)
for reproducible bugs. For highlighting issues, include the content type, a short
source example, and the expected and actual highlighting.

## Set up and verify a change

Use Node.js 24 and the pnpm version in [package.json](package.json).

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Run the same checks as CI before opening a pull request.

```bash
pnpm build
pnpm typecheck
pnpm lint
pnpm test
```

For training, model or packaging changes, see the
[development guide](docs/development.md) and [release guide](docs/npm-release.md).

## Open a pull request

Keep each PR focused and target `main`. Use the
[PR template](.github/pull_request_template.md) to explain the change, list what
you verified, and link related issues or discussions. Use short commit subjects
such as `fix: preserve code spans` or `docs: clarify model setup`.
