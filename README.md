# file-integrity-monitor

Create a baseline of file hashes for a directory, then verify it later. The
report tells you exactly which files were added, removed or modified — the core
of a simple file integrity monitor.

## Features

- Baseline stored as JSON: path, SHA-256, size, mtime.
- Verify reports added, removed and changed files.
- Excludes by glob pattern (`.git`, `node_modules`, `*.log`).
- Exit code `1` when differences are found, for cron or CI.
- Tests use temporary trees.

## Installation

```bash
git clone https://github.com/victor-harden/file-integrity-monitor.git
cd file-integrity-monitor
```

## Usage

```bash
python3 fim.py baseline /etc --out etc-baseline.json
python3 fim.py verify /etc --baseline etc-baseline.json
python3 fim.py verify /etc --baseline etc-baseline.json --json
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
