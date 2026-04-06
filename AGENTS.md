# Agent Guide

This document provides guidance for you when working with the Genesis Scaffolding codebase.

## Required Behavior

- **Before any task** — Read the orientation docs first, even for simple questions
- **Check docs before code** — When investigating something, check the relevant doc first. Only explore code directly if no doc exists or if code behavior differs from docs
- Read docs in the order listed under "Getting Oriented" before offering advice or touching code

## Documentation Structure

The docs are split into two parts:

| Doc Type | Purpose | Location |
|---|---|---|
| **Developer Guides** | Guidelines, processes, and how-tos for working with the project | `docs/developer_guides/` |
| **Architecture** | Descriptions of the architecture — a shortcut to understand the codebase before reading source code | `docs/architecture/` |

## Getting Oriented

When starting work on this project, read these documents in order:

1. **[docs/architecture/scaffolding-overview.md](docs/architecture/scaffolding-overview.md)** — High-level architecture and subsystem overview
2. **[docs/developer_guides/index.md](docs/developer_guides/index.md)** — Tooling, patterns, and conventions for developing in this codebase

## Adapting the Scaffolding

When tasked with using the scaffolding to build or adapt an application for a new use case, **read the adaptation guide before touching any code**:

**[docs/developer_guides/adaptation/decision-process.md](docs/developer_guides/adaptation/decision-process.md)**

This ensures you follow the correct decision process, select the right extensions, and apply the appropriate playbook — rather than improvising an architecture that may not hold up.
