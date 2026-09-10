# Money Trees

Money Trees is a FastAPI budgeting and savings planner with a Streamlit dashboard.

## Run locally

From the project root:

```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal:

```bash
source venv/bin/activate
streamlit run frontend/streamlit_app.py
```

The dashboard expects the API at `http://localhost:8000`. To use another API URL:

```bash
API_BASE_URL=http://localhost:8000 streamlit run frontend/streamlit_app.py
```

## Dashboard areas

- **Monthly finances:** record income and expenses, then view available savings.
- **Allocation & What If:** compare emergency-fund targets through the Python API.
- **Future & AI:** view conservative, base, and optimistic projection scenarios.

The dashboard does not perform financial calculations itself. Monte Carlo simulation and AI explanations are planned for later phases.
