# Configuration System

## Overview

The system uses a layered configuration loading mechanism that resolves settings from multiple sources in priority order, combined with a three-database architecture that separates concerns across system-level, productivity, and memory domains. This design provides flexibility for single- and multi-user deployment, strong isolation guarantees for per-user data, and runtime adaptability for scheduled workloads.

## Config Layers

Configuration is loaded in three successive layers. Each layer performs a deep merge into the accumulated result — later layers override earlier ones on a field-by-field basis without replacing entire sub-trees.

### Layer 1: Environment Variables

The base layer is populated from the process environment. All environment variables carry the prefix `myproject__`. Nested configuration keys use double underscores (`__`) as separators. For example, `myproject__database__host` maps to `database.host`. This layer ensures the system can be bootstrapped from external infrastructure without any files on disk.

### Layer 2: YAML Override File

On top of the environment layer, the system loads a server-level YAML file named `config.yaml` if present at the server root. This file represents site-wide defaults shared across all users on the same deployment — the appropriate place for deployment-specific tunings such as server host, port, or feature flags.

### Layer 3: User-Level Overrides

In multi-user mode, each user may supply their own YAML override file. This layer is loaded from a user-specific location and merged deeply with the accumulated config. It achieves per-user data isolation by overriding paths such as `path.internal_state_dir` and `path.working_directory`, redirecting filesystem reads and writes to user-specific locations.

## Three Databases

The persistent storage layer is split across three purpose-built databases, allowing different retention policies, access patterns, and isolation boundaries to be applied independently.

| Database | Scope | Location |
|----------|-------|----------|
| System DB | Shared across all users | Server root (`myproject.db`) |
| Productivity DB | Per-User | User directory (`users/{user_id}/productivity.db`) |
| Memory DB | Per-User | User directory (`users/{user_id}/memory.db`) |

### System DB

A single shared SQLite database at the server root. It is the system-of-record for all users and contains: user account records, chat session metadata, scheduling entries, and workflow job queues. Its loss affects all users simultaneously.

### Productivity DB

Each user has their own productivity database inside their isolated directory. It holds tasks, projects, and journal entries — the data that is most personal and voluminous. Isolation is enforced by the user-level config override directing its path to a per-user location.

### Memory DB

Each user also has a dedicated memory database alongside the productivity database. This stores event logs and topical memory entries that the agent uses to maintain context across interactions. Like the productivity database, it is fully isolated to its owning user.

## Working Directory Strategy

The working directory is the filesystem location where user-facing operations (file reads, writes, script executions) take place. Its assignment is determined by deployment mode.

**Single-user mode** — the process working directory is used directly. All file operations occur within the same directory tree the server process was started in. No isolation layer.

**Multi-user mode** — each user is assigned a sandboxed working directory at `users/{user_id}/working` relative to a server-provided users directory. This path is set through the deep-merge of `path.internal_state_dir` and `path.working_directory` in the user-level config layer. Each user's agent operates in a completely isolated filesystem view.

## Just-in-Time Context for Scheduling

Scheduled jobs require configuration resolved in the context of the user who owns the job, not the server process at startup. The system resolves user configuration at the moment a scheduled job executes — not when it is queued or when the server starts. If an administrator or user modifies their YAML override file or environment settings, those changes take effect on the next scheduled run without requiring a server restart.

The job queue remains in the shared system database, but the data environments jobs run in are recreated from the current config state at each invocation.

## Related Modules

- `myproject_core.config` — Configuration loading, layered merge, environment variable parsing
