---

## Team Details

- SIDDARTHA AY (PES1UG23AM301) 
- SHRIHAN R (PES1UG23AM297) 
- SAMARTH VINOD HOSALLI (PES1UG23AM261) 
- SIDDARTH REDDY (PES1UG23AM300)

# Docksmith - Lightweight Container Engine

Docksmith is a simplified containerization system inspired by Docker, developed as part of a Cloud Computing mini project. It demonstrates core concepts such as image building, layered architecture, caching, and container-based execution in an isolated environment.

---

## Overview

The project implements a basic container engine that reads instructions from a Docksmithfile, builds images using a layered approach, and executes them in a controlled runtime environment. It is designed to provide a clear understanding of how modern container systems work internally.

---

## Features

- Image building using a Docksmithfile  
- Layer-based architecture for efficient storage  
- Cache mechanism (cache hit and cache miss)  
- Container execution with isolated filesystem  
- Support for environment variables  
- Basic image management (build, list, remove)  

---

## System Workflow

### Build Phase
- Parses Docksmithfile instructions  
- Executes each step sequentially  
- Creates layers for each instruction  
- Stores layers and reuses them when possible  

### Run Phase
- Creates a container from the built image  
- Sets up environment variables  
- Executes the default command  
- Ensures filesystem isolation from host  

---

## Commands

### Build an Image
```bash
docksmith build -t myapp:latest ./sample
