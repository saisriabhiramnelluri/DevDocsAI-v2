<div align="center">
  <h1>DevDocsAI</h1>
  <h3>Multi-Agent Software Intelligence Platform</h3>
  <p><b>Understand any codebase instantly. Chat, analyze, and generate documentation with AI — powered by collaborative multi-agent reasoning.</b></p>
</div>

<br />

DevDocsAI is a comprehensive, AI-powered software intelligence platform that transforms static GitHub repositories into interactive, deeply-understood knowledge bases. By pasting a GitHub URL, developers can instantly chat with their codebase, visualize architecture through auto-generated diagrams, and utilize a suite of AI generators to automate documentation and refactoring tasks.

---

## What's New in V2 (Upgrade from V1)

| V1 (Hybrid RAG)        | V2 (Multi-Agent Architecture)               |
|-------------------------|----------------------------------------------|
| Fixed execution flow    | Dynamic execution planning                   |
| Single reasoning step   | Multi-step reasoning with planning           |
| Static retrieval        | Context-aware, agent-driven retrieval        |
| Limited scalability     | Plug-and-play agent ecosystem                |
| One LLM call            | Multiple specialized reasoning stages        |
| No verification         | Reflection & self-evaluation before response |

> **Core Design Principle:** V2 does NOT replace the Hybrid RAG pipeline of V1 — it wraps it inside a larger, more intelligent agent ecosystem. All existing components (AST Parser, Knowledge Graph, ChromaDB, BM25, RRF) remain intact and are dramatically enhanced by multi-agent coordination.

---

## Key Features

### Multi-Agent AI Chat Engine
DevDocsAI uses a sophisticated multi-agent orchestration layer to dynamically solve complex software engineering tasks:
- **Orchestrator Agent**: Dynamically routes queries to specialized agents based on task complexity.
- **Planning Agent**: Decomposes complex questions into structured execution plans.
- **Retrieval Agent**: Context-aware, hybrid search using Vector embeddings (ChromaDB), BM25, and Graph Enrichment.
- **Repository Agent**: Infers project frameworks, architecture, and language patterns.
- **Architecture Agent**: Auto-generates Mermaid dependency graphs and traverses ASTs.
- **Code & Docs Agents**: Handles deep code analysis, code review, and documentation generation.
- **Reflection Agent**: Validates responses, checks citations, and ensures completeness before returning results.

### Codebase Intelligence
- **Automated Analysis Pipeline**: 10-stage ingestion engine that clones, parses (via Tree-sitter), builds AST dependency graphs, and generates dense vector embeddings in a single pass.
- **Semantic Code Search**: Lightning-fast semantic search across functions, classes, and file contents.
- **Architecture Visualization**: Auto-generated, interactive Mermaid dependency graphs mapping out complex system architectures.
- **Interactive File Explorer**: Deep drill-down capabilities into files, exposing functions, classes, and their immediate dependencies.

### AI Generator Suite
A collection of standalone, production-ready AI tools to automate developer workflows:
1. **Code Comment Generator**: Auto-authors comprehensive JSDoc, Google, and Sphinx docstrings.
2. **Unit Test Generator**: Scaffolds complete, edge-case-aware test suites for Jest, pytest, and JUnit.
3. **UML Diagram Generator**: Instantly generates Mermaid class, sequence, and component diagrams from code snippets.
4. **Code Language Converter**: Idiomatically translates logic between Python, JavaScript/TypeScript, and Go.
5. **Code Optimizer**: Provides AI-driven refactoring suggestions, categorized by performance and security severity.
6. **Swagger/OpenAPI Docs**: Converts raw JSON/YAML specs into polished, human-readable markdown reference documentation.
7. **Release Notes Generator**: Parses raw git commit history into structured, categorized changelogs.
8. **Tree Documentation**: Builds annotated directory trees with AI-inferred folder descriptions.

---

## System Architecture

DevDocsAI employs a multi-agent orchestration layer (powered by LangGraph) on top of a decoupled backend. Agents communicate through a shared memory system and invoke standardized tools.

```text
                          ┌─────────────────────────────────────────────────────┐
                          │              FRONTEND (React + Vite)                │
                          │  Glassmorphic UI, Dashboard, Repo Detail, Gen Hub   │
                          └──────────────────────┬──────────────────────────────┘
                                                 │ REST API + SSE
                          ┌──────────────────────▼──────────────────────────────┐
                          │              BACKEND (FastAPI)                      │
                          │  ┌──────────────────────────────────────────────┐   │
                          │  │         ORCHESTRATOR AGENT (LangGraph)       │   │
                          │  │                                              │   │
                          │  │  ┌────────┐ ┌────────┐ ┌─────────────────┐   │   │
                          │  │  │Planning│ │  Repo  │ │   Retrieval     │   │   │
                          │  │  │ Agent  │ │ Agent  │ │     Agent       │   │   │
                          │  │  └────────┘ └────────┘ └─────────────────┘   │   │
                          │  │  ┌────────┐ ┌────────┐ ┌────────────────┐    │   │
                          │  │  │  Arch  │ │  Docs  │ │  Code Analysis │    │   │
                          │  │  │ Agent  │ │ Agent  │ │     Agent      │    │   │
                          │  │  └────────┘ └────────┘ └────────────────┘    │   │
                          │  │  ┌──────────────────┐                        │   │
                          │  │  │ Reflection Agent │ ← validates & loops    │   │
                          │  │  └──────────────────┘                        │   │
                          │  └──────────────────────────────────────────────┘   │
                          │  ┌────────────────────┐  ┌───────────────────┐      │
                          │  │  Shared Memory     │  │  Tool Registry    │      │
                          │  └────────────────────┘  └───────────────────┘      │
                          │  ┌──────────────────────────────────────────────┐   │
                          │  │  PostgreSQL/SQLite │ ChromaDB │ NetworkX     │   │
                          │  └──────────────────────────────────────────────┘   │
                          └─────────────────────────────────────────────────────┘
                                                 │
                                           ┌────────────┐
                                           │    LLM     │
                                           │  Interface │ (Provider-Agnostic)
                                           └────────────┘
```

---

## Technology Stack

- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Framer Motion, Zustand, Mermaid.js
- **Backend:** FastAPI (Python 3.12+), Celery
- **Data & Storage:** SQLAlchemy, SQLite/PostgreSQL, ChromaDB (Vector DB), NetworkX (Graph)
- **AI & Search:** LangGraph, PydanticAI, LangChain, Provider-Agnostic LLM Interface (Gemini, Groq, OpenRouter), `BAAI/bge-large-en-v1.5` embeddings, rank-bm25

---

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/DevDocsAI.git
cd DevDocsAI/backend

# Set up virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Environment Configuration
cp .env.example .env
# Open .env and set LLM_PROVIDER + API key (e.g., Gemini, Groq, OpenRouter, DeepSeek)

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```
- API available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Open a new terminal instance
cd DevDocsAI/frontend

# Install dependencies
npm install

# Environment Configuration
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start the Vite development server
npm run dev
```
- Application available at `http://localhost:5173`

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.
