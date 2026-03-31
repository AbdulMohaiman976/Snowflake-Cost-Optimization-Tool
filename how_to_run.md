# ❄️ SnowAdvisor: Execution Manual

This guide explains how to set up and run the SnowAdvisor Cost Intelligence API.

---

## 🛠️ 1. Prerequisites

- **Python 3.10+**: Ensure Python is installed.
- **FastAPI & Uvicorn**: Used for the backend server.
- **MongoDB Atlas Cluster**: A cluster is required for report storage.

---

## ⚙️ 2. Environment Setup

1. **Clone/Copy the Code**: Ensure you have the following folder structure:
   ```text
   snowflake/
   ├── api/          # FastAPI logic
   ├── backend.py    # Snowflake pipeline
   ├── analysis.py   # Analysis engine
   └── requirements.txt
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a file named [.env](file:///c:/Users/Abubakar/Desktop/snowflake/.env) inside the `api/` directory ([api/.env](file:///c:/Users/Abubakar/Desktop/snowflake/api/.env)).
   Add the following variables:

   ```bash
   # Secret key for session encryption (Random string)
   SESSION_SECRET_KEY="your-secret-key-here"

   # MongoDB Connection String (from Atlas)
   MONGO_URI="mongodb+srv://<user>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
   MONGO_DB="snowadvisor"
   ```

   > [!TIP]
   > You can use the template provided in [api/.env.example](file:///c:/Users/Abubakar/Desktop/snowflake/api/.env.example).

---

## 🚀 3. Running the Server

Run the following command from the **root directory** of the project:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔍 4. Accessing the API

Once the server is running, you can access the interactive documentation (Swagger UI) at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### How to Run an Analysis:
1. Open the `/docs` page.
2. Locate the **`POST /session/connect`** endpoint.
3. Click **"Try it out"**.
4. Provide your Snowflake credentials in the request body.
5. Click **"Execute"**.

The API will:
- Connect to your Snowflake account.
- Run the intelligence analysis.
- Save the results to MongoDB.
- Return a `session_id` and the full analysis report.

---

## 🛡️ 5. Security Note
SnowAdvisor is **read-only**. It does not perform any `INSERT`, `UPDATE`, or `DELETE` operations on your Snowflake data. It only reads metadata from `ACCOUNT_USAGE` for cost and performance analysis.
