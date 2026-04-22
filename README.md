# Docksmith: A Simplified Docker-Like Build and Runtime System

Docksmith is a lightweight, educational container build-and-run tool implemented in Python. It reproduces core Docker concepts such as image manifests, content-addressed layers, build caching, and isolated runtime execution.

This project was developed as part of a Cloud Computing mini project.

---

## Team Members

- SIDDARTHA AY - PES1UG23AM301  
- SHRIHAN R - PES1UG23AM297  
- SAMARTH VINOD HOSALLI - PES1UG23AM261  
- SIDDARTH REDDY - PES1UG23AM300  

---

## Project Highlights

- Supports Dockerfile-style instructions:
  - FROM
  - COPY
  - RUN
  - WORKDIR
  - ENV
  - CMD  
- Deterministic content-addressed layer digests  
- Build cache with explicit key computation  
- Image lifecycle commands (build, images, run, rmi)  
- Linux namespace isolation using unshare and chroot  
- Implemented using Python standard library  

---

## Repository Structure

cc-proj/
  docksmith/
    builder.py
    cache.py
    cli.py
    images.py
    layers.py
    parser.py
    runtime.py
    store.py
  sample/
    Docksmithfile
    run.sh
  scripts/
    setup_images.py
  main.py
  pyproject.toml
  REPORT.md
  run.sh

---

## Architecture Overview

### Parser Layer
Parses Docksmithfile, removes comments, validates instructions, and produces ordered instructions.

### Build Engine
Executes instructions sequentially:
- FROM loads base image  
- WORKDIR and ENV update state  
- COPY creates layer  
- RUN executes command and snapshots changes  
- CMD stores runtime command  

### Layer System
- Sorted tar entries  
- Zeroed metadata  
- SHA-256 digest generation  

### Runtime Isolation
Uses:
- unshare (user, mount, pid namespaces)  
- chroot  

### State Management
Stored under:

~/.docksmith/
  images/
  layers/
  cache/

---

## Image Manifest Format

{
  "name": "myapp",
  "tag": "latest",
  "config": {
    "Env": ["APP_NAME=DocksmithApp"],
    "Cmd": ["sh", "/app/run.sh"],
    "WorkingDir": "/app"
  }
}

---

## Build Cache Design

Cache key depends on:
- Previous layer digest  
- Instruction  
- Working directory  
- Environment variables  
- File contents (for COPY)  

Cache hit occurs if layer already exists.

---

## CLI Commands

Build:
docksmith build -t myapp:latest ./sample

Run:
docksmith run myapp:latest

List Images:
docksmith images

Remove Image:
docksmith rmi myapp:latest

---

## Setup Instructions

### Prerequisites
- Linux system  
- Python 3.11+  
- uv installed  

---

### Installation

uv sync

---

### Import Base Image

python3 scripts/setup_images.py

---

### Run Demo

chmod +x run.sh  
./run.sh

---

## Sample Docksmithfile

FROM alpine:3.18  
WORKDIR /app  
ENV APP_NAME=DocksmithApp  
ENV APP_VERSION=1.0.0  
COPY . /app  
RUN sh -c "mkdir -p /app/output && echo 'Build OK'"  
CMD ["sh", "/app/run.sh"]

---

## Reproducibility

- Deterministic layer generation  
- Stable hashing  
- Consistent builds  

---

## Limitations

- Linux only  
- No multi-stage builds  
- No networking support  
- No layer deletion handling  

---

## Troubleshooting

- Run setup_images.py if base image missing  
- Use sudo if namespace issues occur  
- Ensure PATH is correctly set  

---

## Additional Documentation

- REPORT.md  
- run.sh  

---

## Conclusion

This project demonstrates the core principles of containerization including image construction, caching, and isolated execution, closely resembling real-world container systems like Docker.

---

## License

This project is intended for academic and educational use.
