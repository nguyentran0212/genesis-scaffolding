# User Tutorial: Developing Workflow

## Introduction

A workflow consists of a sequence of steps to achieve certain outcome. A workflow has a set of inputs. The workflow steps work on these inputs to create the outputs. These steps can be software programs such as fetching a remote API or read a file. These steps can be done by an LLM-based agent itself.

You can think of workflow as a predefined plan to get something done. You define it once, and then you can call it any time you need. You can even tell the system to schedule a workflow to run at certain time on a repeated schedule.

Workflow is written as YAML file and stored in the `workflows/` directory. You don't need to modify source code of the system to add new workflow, though in the current version, you will need to restart the system for the change to be detected.

Workflow steps are programmed in the code of the system. You can think of the workflow steps as "skills" that you can use (e.g., search web, fetch web page, download and parse paper from Arxiv). In order to add new type of workflow steps, you need to modify the source code in the `myproject-core` package. 

In this tutorial, I will explain the idea behind the workflow design and show you how to write new workflows yourself.

## Writing Workflow

### Anatomy of a workflow

Look at the example workflow below. 

```yaml
name: "Summarize Arxiv Paper"
description: "Download an Arxiv paper and summarize it"
version: "1.0"

inputs:
  paper_id:
    type: "string"
    description: "ID of the Arxiv paper"

steps:
  - id: "arxiv_download"
    type: "arxiv_download"
    params:
      arxiv_paper_ids: 
        - "{{ inputs.paper_id }}"

  - id: "paper_summary"
    type: "prompt_agent"
    params:
      agent: "research_summary"
      files_to_read: "{{ steps.arxiv_download.file_paths}}"
      prompts: 
        - "The paper to summary is in your clipboard"
      write_response_to_file: True
      write_response_to_output: True
      output_filename: "paper_summary.md"

  - id: "paper_critic"
    type: "prompt_agent"
    params:
      agent: "research_critic"
      files_to_read: "{{ steps.arxiv_download.file_paths}}"
      prompts: 
        - "The paper to analyze and provide critic is in your clipboard"
      write_response_to_file: True
      write_response_to_output: True
      output_filename: "paper_review.md"


outputs:
  paper_summary:
    description: "Summary of the paper"
    value: "{{ steps.paper_summary.content }}"
  paper_critic:
    description: "Critic of the paper"
    value: "{{ steps.paper_critic.content }}"
  output_path:
    description: "File path to downloaded paper"
    value: "{{ steps.arxiv_download.file_paths }}"
```


This workflow accepts as input a string variable named `paper_id`. Upon running, the workflow engine (either in CLI or in the web server backend, depending on how you run the system), this variable would be filled in and stored in an **internal blackboard** as `inputs.paper_id` variable. The workflow engine ensures that this input variable would have the same type as you defined, meaning if user provides content that cannot be parsed to string to the `paper_id` variable, the workflow engine would reject the input.

The workflow has multiple steps. Each step has:
- `id`: uniquely identifier of this step. 
- `type`: the type of workflow step. If you refer to a workflow step type that is not known by the system, the workflow would be rejected.
- `condition`: a string that contains a Jinja2 expression. If it resolves to false, step would be skipped. If it resolves to true or if no condition is provided, workflow step would run.
- `params`: a dictionary of inputs to the workflow steps. Each type of workflow step has its own types of parameters, but there are some common parameters across all workflow steps. I will provide more details of the workflow steps in the next section. 

The workflow has outputs. The web server and frontend would use this information to present outputs to you after running the workflow.

You might note the fields such as `"{{ steps.arxiv_download.file_paths}}"` scattered across the YAML. From the perspective of the system when it parse the workflow YAML, these fields are simply strings. However, at runtime, the system would treat this string as Jinja2 template and use the content from the **internal blackboard** of the workflow to fill in template, forming complete `params` dictionary to be passed to the workflow step. The workflow step itself would have another validation to ensure that all the params it requires are provided and they are of the right type.


The output of the workflow step is then registered on the blackboard and, optionally, written down to the internal directory. The following step then can read from blackboard or from the internal directory as input.

The final output of the workflow also uses the content from blackboard or internal directory as the output.

Only files that are stored in the output directory are accessible to user by the end.


### Understanding the workflow blackboard and internal directory

Workflow steps pass information between each other using two mechanisms: a blackboard, and a shared internal directory

Here is how blackboard of the Summarize Arxiv Paper workflow after a completed run:

```json

{
  "inputs": {
    "paper_id": "2602.14337"
  },
  "steps": {
    "arxiv_download": {
      "content": [
        "details of the downloaded papers"
      ],
      "file_paths": [
        "path/to/markdown/file"
      ],
      "pdf_paths": [
        "path/to/pdf/file"
      ],
      "md_paths": [
        "path/to/markdown/file"
      ]
    },
    "paper_summary": {
      "content": [
        "summary of the paper"
      ],
      "file_paths": [
        "path/to/response/markdown/file"
      ]
    },
    "paper_critic": {
      "content": [
        "critic of the paper"
      ],
      "file_paths": [
        "path/to/response/markdown/file"
      ]
    }
  }
}
```

The workflow inputs are stored in the `inputs` object

The intermediate outputs of workflow steps are stored in the `steps` object, which contains multiple sub-objects. Each sub-object contains the outputs from the corresponding workflow step. In general, each step returns an array of string output and an array of paths, should it writes files down.

### Intuition of workflow

You should think of workflow as a data-flow that operates on a list of inputs rather than a control-flow: series of instructions that applies to individual input item.

For example, imagine you have the task of writing a blog post about a research paper and you want your local LLM to do this. You could try to one-shot this task, but the writing would generally be short and generic. So, you need the break the task into smaller phases: first, you get LLM to generate an outline (and maybe review the outline and adjust until you are happy with it), then, for each section, you can instruct your LLM to write based on the source material. Finally, you will string these sections together into a complete draft, and run one last pass through LLM to edit and finallize, before you do the final human-in-the-loop verification.

If you implement this process as a series of instruction, you would need to have loop and branching features to handle input item one by one (e.g., each section of the outline).

The workflow in my system encourage you to think in terms of data pipeline rather than instruction by instruction. Here is how it works:
1. Given the writing topic and source material, the first step (writing outline) acts as a **projection** or fan-out step that turn the input (writing topic) into a list, each list item contains the details for one section.
2. The drafting step is akin to a **map** operation. It takes a list of instructions to write sections and transform it to a list of written sections.
3. The finalisation step is akin to a **reduce** operation. It takes a list of written section and reduces the list down to one item, which is the final draft.
4. The editing step is like a map operation that applies on one item to transform the final draft (input) to the edited version (output). 
5. The final output is then routed to the workflow output and presented back to you.

As you can see, it's simpler to think about and simpler to write workflow this way. And no loop is needed to iterate through elements. And if your LLM and API support, you can performs the map step in parallel to further speed up the process.


## Understanding Workflow steps

Simply put, a workflow step accepts a dictionary of `params`, do something with it, and return a set of outputs. It might write files to internal storage and output storage if necessary.

### Common workflow steps inputs

```python
class TaskParams(BaseModel):
    """Common schema for all workflow task parameters."""
    files_to_read: list[Path] = []

    sub_directory: str | None = None
    write_response_to_file: bool = True
    write_response_to_output: bool = False
    output_filename: str = ""
    output_filename_prefix: str = ""
```


Every workflow step has the following parameters:
- `files_to_read`: a list of python Path objects telling a step which files to read. This list can come from a prior workflow step, or from inputs from user.
- `write_response_to_file`: determine whether the step should write content down in a file or just store the output in the blackboard
- `write_response_to_output`: determine whether the step should also copy the written content to the output directory
- `sub_directory`: if the step writes down a file, it would be the files underneath this sub directory in the internal directory or the output directory
- `output_filename`: if there is only one file to write, this name would be used.
- `output_filename_prefix`: if there are many files to write, this prefix would be added to the file name

### Common workflow step output

```python
class TaskOutput(BaseModel):
    """Common schema for all workflow task output."""

    model_config = ConfigDict(extra="ignore")
    content: list[str]
    file_paths: list[Path] | None = None
```

Every workflow step has the following output:
- `content`: a list of string outputs (e.g., response from LLM for each input prompt)
- `file_paths`: a list of paths to files that the workflow steps write in the internal directory. Could be empty if the workflow step does not write file.

### Connecting workflow steps

You can pipe the `file_paths` output from a workflow step directly to the `files_to_read` of the subsequent steps in the workflow.

You can pipe the `content` output from a workflow step directly to a params in a subsequent steps that receive a list of string.

You can use Python list notation to access components of the list. For example, if a subsequent component accepts only one string, you can use `"{{ steps.prior_step.content[0] }}"` to use only one string output from the previous step.


## References of current workflow steps:

### Prompt Agent

**What it does:** take an array of input prompts and an array of files to read. Each input prompt would be processed by a required LLM agent in **one** step to generate response. The input files are added to the clipboard of the agent to use context for responding. An array of responses is returned. 

**Inputs**:
```python
class PromptAgentTaskParams(TaskParams):
    agent: str # ID of the agent to use for this prompt
    prompts: list[str] # List of input prompts
    output_filename: str = "output.md" # Default name of the output files. DO NOT REPLACE THIS WITH ""

```
**Outputs**:
- `content`: a list of string of responses
- `file_paths`: a list of Path pointing to response files written to disk

### File Ingest

**What it does:**: symlink or copy a list of input files to the internal directory of the workflow so that they are available for other steps.

**Inputs**: 
- `files_to-read`: if the paths are absolute, the system would try to read from the path and throw exception if the path is not available or unsafe. If the path is relative, the system would try to read from the `inbox` directory of the current working directory specified in the settings.

**Examples:**

```yaml
steps:
  - id: "file_ingest_step"
    type: "file_ingest"
    params:
      files_to_read: "{{ inputs.input_files }}"
```


### Web Search

**What it does:** take one query, performs search using DDGS, and fetches the web pages of search results, and return a list of articles parsed to markdown.

**Inputs:** 

```python
class WebSearchTaskParams(TaskParams):
    query: str
    number_of_results: int = 10
    output_filename_prefix: str = "search_results"
```

**Outputs:**
- `content`: a list of string storing the fetched and parsed articles
- `file_paths`: list of paths to markdown files stored in the internal directory

### Arxiv Download

**What it does:** Download articles from arxiv based on given ID. Automatically convert PDF to markdown as well.

**Inputs:**

```python
class ArxivDownloadTaskParams(TaskParams):
    # Accept a list of paper IDs
    arxiv_paper_ids: list[str]
    write_response_to_output: bool = True
    output_filename_prefix: str = "arxiv_"
```

**Outputs:**
- `content`: a list of markdown content of the retrieved papers
- `file_paths`: a list of path to the stored markdown files
- `md_paths`: a list of paths to the stored markdown files
- `pdf_paths`: a list of paths to the stored pdf files

### Arxiv Search

**What it does:** take one query, perform search on Arxiv, and retrieve PDF and markdown of relevant papers.

**Inputs:**

```python
class ArxivSearchTaskParams(TaskParams):
    query: str
    max_results: int = 5
    output_filename_prefix: str = "arxiv_search_"
    write_response_to_output: bool = True
```


**Outputs:**
- `content`: a list of markdown content, each has a summary and title of one of the found papers
- `file_paths`: a list of path to the stored markdown files
- `md_paths`: a list of paths to the stored markdown files
- `pdf_paths`: a list of paths to the stored pdf files
