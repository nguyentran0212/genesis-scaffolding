# Developer Guideline

This document provides instructions for developers and AI agents who try to add features, fix bugs, or adapt the codebase to different use cases and contexts.

-----

## How to run the code 

### Prerequisite to build and run the code

List of hardware and software requirements for running the code in developer mode

### Required configurations

Details regarding the necessary configuration files or variables for the code to run, what they means, and how to set them.

### Commands

List of commands to start the system in dev and prod mode.

-----

## How to test the code

### Design of QA System

Details regarding the standard, process, and tooling for code quality of the project. CI workflow details are also described here if available.

### Commands

List of commands to lint and test the project.

-----

## How to build and release the code

### Release Artefacts and Processes

Details regarding the artefacts that are considered releases of this project. If available, also provide details regarding tagging scheme and release plan for the codebase.

### Commands

List of commands to build artefacts

-----

## Development Conventions

### Understand the architecture before code

Before implementing any new feature or bug fix, ensure that you understand the following thoroughly:

- Runtime architecture of the system: Runtime components, how they are deployed, how they connect with each other, and important data flows and control flows involving these components
- Module structure of the codebase: main modules making up the codebase of the system, their functionality, how runtime components are mapped onto code modules
- Tooling of the codebase: correct tools and commands to run and check the code

To understand the architecture, first check the architecture documentation. Then, read any source code module you consider necessary for your task to confirm the details of the code.

### Plan and articulate the plan before code

Always plan thoroughly before performing code changes. When you plan, you should always consider the following:

- Which runtime component(s) need to be added or modified to implement the new feature or bug fix?
- Which code module(s) would be impacted by the change you are going to make?
- Is there existing code module(s) you can import to implement your task or do you need to write new ones?
- If you need to implement new logic or module, would you be replicating some existing code? If that's the case, can you find a way to adapt the existing logic for your task instead? (See the DRY principle below)
- Do you need to add any configuration to the system to support your proposed change? If so, which are the configurations to add or modify, and how do you plan to implement it?
- What would be the side effect of your proposed change? Would your change break the existing, functional codebase?
- Is there any new tests you need to add to the codebase to test your proposed change?
- Do you need to update documentation to capture your proposed change?

For human developers and AI agents that review plans: it's your responsibility to ensure that the change does not violate the architectural design principles of the codebase.

### Don't Repeat Yourself (DRY)

Do not duplicate logic, module, UI components with your proposed code change.

Adapt your proposed new code to work with the existing logic, modules, components if possible.

Refactor existing logic, modules, components, into shared utilities if necessary. 

For example: imagine the codebase already have the logic for renewing authentication token, but this logic only works in the server action because it relies on setting browser sessions, therefore you cannot use it in your new edge component. Instead of writing a replica of logic to renew token in the edge component, you can: (1) refactor the token renew logic to a shared utility, (2) refactor the server action to call the utility to renew token, and then set the session, (3) write your edge component to use the utility to renew token, and then set the HTTP response header. With this design, the logic to renew token is not duplicated across the codebase.

### Keep It Simple

Do not add abstraction layers and modules to "future-proof" the project. If you are only going to add a new feature, do not add arbitrary abstract classes, abstract interfaces, complex inheritance chain for the sake of "clean code".

Your design need to prioritise readability and maintainability:

- Ensure that codes within each module contribute to a single functional unit or area of the code
- Split code modules only when this decision increases the cohesiveness and facilitate reuse of logic (DRY principle above)
- Use type (with typescript codebase) or schema (with python codebase) to standardize inputs, outputs, and commonly used data objects of module

### Don't Breaking Working Code

Assume that existing code not directly related to the proposed update or bug fix is functional. Avoid making change to existing components and modules.

For example: imagine you are trying to add horizontal scrolling to an existing complex, hierarchical component. It is desirable to modify code at the wrapper level around the component, rather than changing the code from inside the component, as you might not understand the prior design decisions and assumptions when this component was built.


### Master branch must past the QA Checks

Run code quality check command before starting to work on the codebase to notice any pre-existing issues.

Run code quality check command after finishing your code change, and fix any issues that are caused by your code change. Do not return the code for review before you have finished your quality check.

### No Partial Git Commit

Do not add or commit to git before or during your code change process. 

If you are an AI agent, this instruction applies to both you and your subagents.

### Human Developer Signing Off Commit

The final git commit implementing the feature or code change must be reviewed and signed off by a human developer, not AI agent.

### Document Your Change

Document any change to runtime and static architecture in the architecture docs directory.

If you change leads to any changes in the developer practice, update the developer guideline directory content.
