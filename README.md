# Product Review Intelligence Platform (litmus7_project)

## The Problem
The immense volume of unstructured product reviews makes manual analysis inefficient for businesses seeking actionable insights.

## The Solution
- Instead of prompting an entire list of reviews, we use a **divide-and-conquer** approach.
- **Example**: For 1000 reviews, the system chunks the reviews into smaller chunks (e.g., 100 reviews each), and extracts the business-related context.
- These chunks are processed by parallel sub-agents of a root model.
- The root model then aggregates the results from the sub-agents and filters the data to ensure the best results and quality.

![Alt Text](pipeline-digram.png)

---

## Run Setup Guide

### 1. Create Environment (First Time)
```bash
python3 -m venv .venv
```

### 2. Activate the Environment
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (.env)
Configure the following variables in a `.env` file at the root of the project:
* `GEMINI_API_KEY`: Your Gemini API key (required for Gemini model execution).
* `LOCAL_CONCURRENCY_LIMIT`: Controls parallel API requests to prevent rate limits (default: `4`).
* `MAX_REVIEWS_TO_ANALYZE`: Maximum number of reviews to process at once (default: `100`).
* `MODEL_TEMPERATURE`: Optional temperature for the models (default: `0.0`).
* `MODEL_SEED`: Optional random seed for reproducible outputs (default: `42`).
* `MODEL_MAX_TOKENS`: Maximum output tokens for aggregator (default: `8192`).
* `PARALLEL_MODEL_MAX_TOKENS`: Maximum output tokens for parallel sub-agents (default: `4096`).

### 5. Start the FastAPI Backend
```bash
uvicorn app.main:app --reload
```

### 6. Start the Streamlit Frontend
```bash
streamlit run streamlit_app.py
```

### 🧠 Performance & Rate Limits
This pipeline is designed for massive datasets (2000+ reviews). It includes built-in rate-limit protections:
- **Concurrency Queues:** The `LOCAL_CONCURRENCY_LIMIT` ensures that only a set number of API requests run at exactly the same time, keeping you under rate limits.
- **Auto-Retries:** The pipeline leverages Google ADK native retry policies to automatically handle transient API errors.