# Project Goals

Genesis Scaffolding serves three complementary purposes: a production application scaffolding, a demonstration application, and a research laboratory for agent systems.

---

## For Developers: The Scaffolding

The goal of Genesis Scaffolding is to give you a well-engineered, layered foundation for building production-ready LLM-powered applications. Rather than prescribing a single path, it offers a menu of capabilities — an agent harness, a workflow engine, a productivity system, a scheduling layer, a FastAPI backend, a NextJS frontend — that you can adopt piecemeal as your application grows.

This codebase aims to be understandable and maintainable by both human developers and LLM-based coding agents. Every layer is designed to be readable first, extensible second. The architecture is thin and close to the logic — no unnecessary abstraction layers hiding what's really happening.

The scaffolding is deliberately opinionated about the right way to do things, but flexible about which things you actually want to do:

- **Clarity over Abstraction:** We trade off cleverness for legibility. When you read a piece of code, you should understand exactly what it does without chasing through five levels of generics.
- **Well-defined Dependencies:** No circular dependencies. Every package and module has a narrowly defined purpose and a clear interface to the layers above and below it.
- **Canonical Tooling:** We pick modern, standard libraries (`uv`, `Pydantic`, `pydantic-settings`, `FastAPI`, `litellm`, `NextJS`) and use them consistently, so the patterns you learn in one part of the codebase transfer to the rest.
- **Pick Your Complexity:** Start with the core Python monorepo and a FastAPI backend. Add the agent harness when you need it. Add the workflow engine when your agents need to do multi-step tasks. Add the productivity system when you need a task and calendar layer. You don't have to commit to everything at once.

---

## For Users: The Demo App

Out of the box, Genesis Scaffolding includes a fully functional **personal AI assistant** that demonstrates every capability the scaffolding provides: an agent with tool calls and persistent memory, deterministic workflows that agents can invoke, cron-scheduled tasks, a productivity system (tasks, projects, calendar, journal), multi-user server mode with per-user config overrides, and support for a variety of LLM providers configurable from the frontend.

This demo app is not the product — it is an illustration of what the scaffolding makes possible. You can use it as a starting point and customize it heavily, or you can strip out everything except the parts you need and build something entirely different. The scaffolding exists so you don't have to solve the problems we've already solved: how to run an agent loop, how to define a workflow, how to manage multi-user sessions, how to bridge a Python backend with a NextJS frontend. You get to focus on what your application actually does.

---

## A Laboratory for Agent Research

Beyond being a scaffolding for applications, Genesis Scaffolding is also a **research laboratory** for experimenting with agent techniques. The architecture is designed to make it easy to swap in different implementations of core subsystems — different agent loops, different memory systems, different RAG strategies, different tool-calling patterns — and measure the effects.

Our primary research focus is **making small and medium language models practical**: getting reliable, efficient, and safe behavior from models that can run on consumer hardware. We believe that with the right framework support — prompt engineering, workflow offloading, token-budget management via clipboard, persistent memory — the gap between SLMs and large proprietary models narrows considerably for many real-world tasks.

Our approach to making agents reliable is based on a few ideas we've found work in practice:

- **Instruction Following over Planning:** Modern LLMs are highly capable of following instructions and handling long contexts. However, they struggle with reliable multi-step planning and complex tool-use (such as file editing). These gaps often lead to high latency and unreliable outcomes.
- **Offloading Orchestration to the Framework:** In many real-world tasks, the optimal execution path is already known. By defining this process as a deterministic workflow, we remove the burden of planning from the model. This allows the model to focus entirely on the content of the task rather than the management of the process.
- **Native Terminal Integration:** By making workflows executable from the CLI, the project enables advanced use cases such as batch processing of documents or scheduling recurring tasks via `cron`.

The demo application serves as our testbed: everything we implement for the scaffolding, we validate against real agent sessions. The agent harness, the clipboard optimizer, the memory system, the workflow engine — all of these are pieces of a larger research agenda, not afterthoughts.
