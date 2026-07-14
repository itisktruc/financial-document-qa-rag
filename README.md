# Financial Document Intelligence Assistant

## Overview
This project is a Financial RAG (Retrieval-Augmented Generation) Chatbot designed to process and query complex financial documents intelligently. 

## Dataset
* **Domain:** Finance
* **Document Types:** 10-K/10-Q reports, credit agreements (hợp đồng tín dụng), and prospectuses (bản cáo bạch)

## Architecture
* **Core Techniques:** Layout/Table-aware Parsing, Hierarchical Chunking, Metadata Enrichment, Hybrid Search (BM25 + Dense), Cross-Encoder Reranking, HyDE, Semantic Query Routing, Traceable Citations, and Semantic Caching
* **RAG Framework:** LlamaIndex / LangChain / LangGraph

## Tech Stack
* **PDF Parser:** Docling / LlamaParse
* **Vector DB:** Qdrant (or Pinecone / Milvus)
* **Reranker:** bge-reranker-large or Cohere Rerank API
* **LLM & Embeddings:** GPT-4o-mini, Llama 3 (Groq API), OpenAI/Claude API
* **Evaluation:** Ragas / TruLens
* **Backend & Cache:** FastAPI + Redis
* **Frontend:** Streamlit / React

## Setup
1. Clone the repository: `git clone <repo-url>`
2. Create and activate a Python virtual environment (e.g., `python -m venv .venv`).
3. Install the required dependencies: `pip install -r requirements.txt`
4. Start the local Vector Database: `docker compose up -d qdrant`

## Run
1. Ensure your virtual environment is active.
2. Ensure Docker containers are running.
3. Execute the main application file (e.g., `python src/app.py`).

## Evaluation
* Automated testing is handled via Pytest.
* Retrieval and Generation evaluation metrics are managed via Ragas / TruLens.

## Team Members
* A
* B
* C
* D
* E