# SnowAdvisor React Dashboard

This is the new, premium React-based frontend for SnowAdvisor. It is built with React 18, Vite, and Tailwind CSS, featuring modern UI patterns inspired by TailAdmin and CoreUI.

## ✨ New Features
*   **Aesthetic UI**: Modern dark theme with glassmorphism and smooth animations.
*   **Health Score Visualization**: Large, beautiful indicators for your account health grades.
*   **Interactive Tables**: Sortable and highlight-driven warehouse and query tables.
*   **Visual Charts**: Built-in Recharts for credit trends and workload distribution.
*   **AI Insight Layer**: Dedicated components for LLM recommendations and agent plans.
*   **Session Management**: Faster session loading and state persistence.

## 🚀 How to Run

### 1. Prerequisites
Ensure you have the following installed:
*   Python 3.8+
*   Node.js 18+
*   MongoDB (or local JSON fallback as configured in the backend)

### 2. Start the Backend (FastAPI)
Open a terminal in the root directory and run:
```powershell
python -m uvicorn api.main:app --reload --port 8000
```

### 3. Start the Frontend (React Vite)
Open **another** terminal in the root directory:
```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at: **http://localhost:3000** (or whatever port Vite selects).

---
*Note: The original Streamlit app (`app.py`) is still functional but is now deprecated in favor of this React version.*
