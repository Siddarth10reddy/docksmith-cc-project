# Docksmith: A Simplified Docker-Like Build and Runtime System

Docksmith is a lightweight, educational container build-and-run tool implemented in Python. It reproduces core Docker ideas such as image manifests, content-addressed layers, build caching, and isolated runtime execution, while remaining small enough to understand end-to-end.

This project was built as a Cloud Computing mini project.

## Team Members

- SIDDARTHA AY - PES1UG23AM301
- SHRIHAN R - PES1UG23AM297
- SAMARTH VINOD HOSALLI - PES1UG23AM261
- SIDDARTH REDDY - PES1UG23AM300

## Project Highlights

- Supports six Dockerfile-style instructions through `Docksmithfile` parsing:
	- `FROM`
	- `COPY`
	- `RUN`
	- `WORKDIR`
	- `ENV`
	- `CMD`
- Produces deterministic content-addressed layer digests.
- Implements build cache with explicit key computation from build state.
- Provides image lifecycle commands (`build`, `images`, `run`, `rmi`).
- Uses Linux namespace isolation (`unshare` + `chroot`) to execute commands inside assembled root filesystems.
- Uses only Python standard library for core implementation.

## Repository Structure

```text
cc-proj/
	docksmith/
		__init__.py
		builder.py      # Build engine for instructions and layer generation
		cache.py        # Cache key computation and cache index operations
		cli.py          # CLI entry point and command dispatch
		images.py       # Image listing and removal helpers
		layers.py       # Tar/delta layer creation and extraction
		parser.py       # Docksmithfile parser and validation
		runtime.py      # Linux isolated command runner
		store.py        # Persistent store layout and JSON I/O
	sample/
		Docksmithfile   # Sample image definition
		run.sh          # Sample runtime script used by CMD
	scripts/
		setup_images.py # One-time Alpine base image import
	main.py
	pyproject.toml
	REPORT.md
	run.sh            # End-to-end demo script
```

## Architecture Overview

### 1. Parser Layer

`docksmith/parser.py` reads a `Docksmithfile`, strips comments/blank lines, supports backslash continuations, validates instruction names, and returns an ordered instruction list with source line numbers.

### 2. Build Engine

`docksmith/builder.py` executes instructions in sequence:

- `FROM` loads a base image manifest from local storage.
- `WORKDIR` and `ENV` update in-memory configuration state.
- `COPY` creates a delta tar layer from context files.
- `RUN` executes a command in isolated rootfs, snapshots changes, and creates a delta tar layer.
- `CMD` stores default runtime command in image config.

At completion, a manifest is generated and stored in the local image store.

### 3. Layer System

`docksmith/layers.py` ensures reproducible layer output by:

- Sorting tar entries lexicographically.
- Zeroing mutable metadata (`mtime`, `uid`, `gid`, owner names).
- Storing uncompressed tar bytes.

Layer digest is SHA-256 over raw tar bytes.

### 4. Runtime Isolation

`docksmith/runtime.py` uses Linux primitives:

- `unshare --user --map-root-user --mount --pid --fork`
- `chroot <rootfs>`

This is used both for `RUN` during image build and `docksmith run` for container execution.

### 5. State Management

`docksmith/store.py` stores all runtime/build data under `~/.docksmith/`:

```text
~/.docksmith/
	images/        # JSON manifests
	layers/        # content-addressed layer tar files
	cache/
		index.json   # cache_key -> layer_digest mapping
```

## Image and Manifest Format

Each image is represented by a manifest:

```json
{
	"name": "myapp",
	"tag": "latest",
	"digest": "sha256:<manifest_hash>",
	"created": "2026-04-22T00:00:00Z",
	"config": {
		"Env": ["APP_NAME=DocksmithApp", "APP_VERSION=1.0.0"],
		"Cmd": ["sh", "/app/run.sh"],
		"WorkingDir": "/app"
	},
	"layers": [
		{
			"digest": "sha256:<layer_hash>",
			"size": 12345,
			"createdBy": "COPY . /app"
		}
	]
}
```

Manifest digest is computed by serializing the same structure with `digest` temporarily set to empty string and hashing that canonical JSON.

## Build Cache Design

Cache keys are SHA-256 of combined build-state inputs:

- Previous layer digest (or base manifest digest for first layer-producing step)
- Instruction text (for example: `RUN apk add curl`)
- Current `WORKDIR`
- Current sorted `ENV` state
- For `COPY`, source file content hashes

Cache hit condition:

- Key exists in cache index
- Referenced layer file exists on disk

If any step misses cache, downstream layer-producing steps are forced misses in that build pass.

## CLI Reference

After installation, use:

```bash
docksmith build -t <name:tag> [--no-cache] <context>
docksmith images
docksmith rmi <name:tag>
docksmith run [-e KEY=VALUE ...] <name:tag> [cmd ...]
```

### Command Examples

```bash
# Build sample image
docksmith build -t myapp:latest ./sample

# List local images
docksmith images

# Run image using CMD from manifest
docksmith run myapp:latest

# Override environment variable at runtime
docksmith run -e APP_NAME=Overridden myapp:latest

# Remove image
docksmith rmi myapp:latest
```

## Setup Instructions

### Prerequisites

- Linux host (runtime isolation depends on `unshare` and `chroot`)
- Python 3.11+
- `uv` (recommended for environment/package management)
- Internet access once, for base image import

### Installation

From project root:

```bash
uv sync
```

### Import Base Image (One Time)

```bash
python3 scripts/setup_images.py
```

This imports `alpine:3.18` into the local Docksmith store.

### End-to-End Demo

Run the provided script:

```bash
chmod +x run.sh
./run.sh
```

The demo script performs cold/warm builds, cache invalidation check, image listing, runtime execution, environment override test, isolation check, and image removal.

## Sample Docksmithfile

`sample/Docksmithfile` demonstrates all supported instructions:

```dockerfile
FROM alpine:3.18
WORKDIR /app
ENV APP_NAME=DocksmithApp
ENV APP_VERSION=1.0.0
COPY . /app
RUN sh -c "mkdir -p /app/output && echo 'Build OK for' $APP_NAME > /app/output/info.txt && echo 'Built successfully'"
CMD ["sh", "/app/run.sh"]
```

## Reproducibility Guarantees

Docksmith is designed for stable outputs across identical rebuilds on the same machine:

- Deterministic tar entry order
- Zeroed tar metadata
- Stable manifest JSON structure
- Preserved `created` timestamp on full cache-hit rebuilds

## Known Limitations

- Linux-only runtime implementation
- No whiteout support for deletions in RUN delta layers
- No layer reference counting on `rmi`
- No networking/volume/resource limit feature set
- No multi-stage build support

## Troubleshooting

- If `build` fails with missing base image, run `python3 scripts/setup_images.py`.
- If unprivileged namespaces are blocked (common on some Ubuntu/AppArmor setups), the runtime attempts a `sudo unshare` fallback.
- If `docksmith` command is not found after `uv sync`, run through the virtual environment binary or ensure script entry points are in PATH.

## Additional Documentation

- Detailed implementation report: `REPORT.md`
- Demo script walk-through: `run.sh`

## License

This project is intended for academic and educational use.
