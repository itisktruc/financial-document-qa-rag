# Project Structure

## Overview

This project follows a modular architecture for building a Financial Document Intelligence system based on Retrieval-Augmented Generation (RAG). Each component is organized into a dedicated directory to improve maintainability, scalability, and collaboration.

## Directory Structure

```text
financial-document-intelligence/
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
│
├── src/
│   ├── parser/
│   ├── preprocessing/
│   ├── chunking/
│   ├── embedding/
│   ├── retrieval/
│   ├── reranker/
│   ├── generation/
│   └── evaluation/
│
├── notebooks/
├── reports/
├── docs/
├── tests/
├── scripts/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Directory Descriptions

### data/

Stores all datasets used throughout the project.

* **raw/**: Original, unmodified financial documents.
* **processed/**: Cleaned and preprocessed data ready for indexing.
* **evaluation/**: Benchmark datasets and evaluation files.

### src/

Contains the source code for the RAG pipeline.

* **parser/**: Extract text from PDF and other document formats.
* **preprocessing/**: Text cleaning and normalization.
* **chunking/**: Split documents into manageable chunks.
* **embedding/**: Generate vector embeddings.
* **retrieval/**: Retrieve relevant document chunks.
* **reranker/**: Re-rank retrieved results.
* **generation/**: LLM prompt construction and answer generation.
* **evaluation/**: Evaluation metrics and benchmarking.

### notebooks/

Jupyter notebooks for experimentation and analysis.

### reports/

Generated reports, figures, and experiment results.

### docs/

Project documentation.

### tests/

Unit and integration tests.

### scripts/

Utility scripts for data processing, indexing, and automation.

## Root Files

* **Dockerfile**: Container definition.
* **docker-compose.yml**: Multi-container configuration.
* **requirements.txt**: Python package dependencies.
* **pyproject.toml**: Project configuration.
* **README.md**: Project overview and setup instructions.
