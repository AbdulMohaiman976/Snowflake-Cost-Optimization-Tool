# SnowAdvisor System Architecture & Workflow Guide

This guide explains the inner workings of the **SnowAdvisor Backend API**, from the moment a user enters credentials to how the data is analyzed and stored securely.

---

## 1. The "Connect" Flow (How Sessions Work)

When a user submits their Snowflake credentials, several things happen in the background:

### A. Credential Handling (The "Secret" Step)
- **Input**: The API receives your [account](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py#100-386), `username`, `password`, `role`, and [warehouse](file:///c:/Users/Abubakar/Desktop/snowflake/analysis.py#73-287).
- **Processing**: We use these credentials **IMMEDIATELY** to connect to Snowflake and pull your data.
- **Security**: **The password is NEVER saved to any database.** It stays in the server's RAM for a few seconds and is erased once the data is pulled.
- **Sensitive Info**: We only save your "Account Name," "User Name," and "Role" into MongoDB so you can see your history later.

### B. Session Token Creation (The "Encrypted" ID)
Each user gets a unique **Session ID** (a long string of random letters).
- **Encryption**: We use **Fernet (AES-128)** encryption. We take a simple ID (like `12345`) and turn it into a secure, encrypted token.
- **Where it is stored**: The **ID** is stored in MongoDB. The **Token** (the encrypted version) is sent to you.
- **Why?**: This ensures that even if someone sees your Token, they cannot guess what your real ID is or access other people's data.

### C. Multi-User Access (Scalability)
The system is built to handle many users at the same time:
- **Statelessness**: Every time you call the API, you send your Session Token. The API decrypts it, looks up **ONLY** your data in MongoDB, and returns it.
- **Concurrency**: Because we use **FastAPI (Asynchronous)** and **MongoDB (Multi-connection)**, User A and User B can both run an analysis at the exact same millisecond without any interference.

---

## 2. Tab-by-Tab Breakdown (The Intelligence Engine)

Every time you "Connect," the [analysis.py](file:///c:/Users/Abubakar/Desktop/snowflake/analysis.py) script runs a "Health Check" by looking at different areas:

| Tab | What it shows | How we calculate it |
| :--- | :--- | :--- |
| **Overview (Health)** | A grade (A-F) for your account. | Weighted average of Security + Cost + Performance scores. |
| **Warehouses** | If your warehouses are too big or small. | We look at **Queue Time** (too small) and **Spillage** (memory issues). |
| **Queries** | Your heaviest, slowest queries. | We rank queries by `execution_time` and `credits_used`. |
| **Anomalies** | Unexpected spend spikes. | We compare **Today's Credits** vs the **Last 7 Days Average**. If it's >2x higher, it's an anomaly. |
| **Cost Analysis** | Who is spending the most money? | We break down credits by **User**, **Role**, and **Warehouse**. |
| **Storage** | Waste from old or bloated tables. | We look at `active_bytes` vs `time_travel_bytes` for every table. |
| **Users & Security** | MFA and Login failures. | We check if MFA is off and count how many times people failed to login. |
| **Unused Objects** | Tables that haven't been touched. | We find tables where `LAST_ALTERED` is > 90 days ago. |
| **Cloud Services** | Credits for background tasks. | We find when you pass the 10% free cloud services threshold. |
| **Notebooks** | Activity in Snowflake Notebooks. | We track execution counts and recent run dates. |
| **Auto-Suspend** | Idle warehouses wasting money. | We check if `AUTO_SUSPEND` is set too high (e.g., > 10 minutes). |

---

## 3. The Database (MongoDB Integration)

We use **MongoDB Atlas** (a cloud database) to remember your history.

### A. Moving from "Temporary" to "Production"
Currently, the app uses a temporary cluster I set up for you. To change it:
1.  **Open the File**: Browse to [api/.env](file:///c:/Users/Abubakar/Desktop/snowflake/api/.env).
2.  **Update the URI**: Change `MONGO_URI` to your own MongoDB connection string.
3.  **Update the Name**: Change `MONGO_DB` to your preferred database name.

### B. What is stored in the DB?
We store a single document per session that looks like this:
```json
{
  "_id": "6789...",
  "account_name": "ABC12345",
  "runs": [
    { "analyzed_at": "...", "health": 85, "cost": 10.5, ... },
    { "analyzed_at": "...", "health": 90, "cost": 9.2, ... }
  ]
}
```
As you run the tool more often, the [runs](file:///c:/Users/Abubakar/Desktop/snowflake/analysis.py#1452-1509) array grows, allowing you to see your **Health History** over time.

---

## 4. The Complete Data Flow

1.  **Frontend**: You send your Snowflake credentials.
2.  **API ([main.py](file:///c:/Users/Abubakar/Desktop/snowflake/api/main.py))**: Receives them and calls [backend.py](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py).
3.  **Backend ([backend.py](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py))**: Pulls raw JSON data from Snowflake.
4.  **Analysis ([analysis.py](file:///c:/Users/Abubakar/Desktop/snowflake/analysis.py))**: Turns raw data into "Intelligence" (Calculates scores, finds anomalies).
5.  **Storage ([storage.py](file:///c:/Users/Abubakar/Desktop/snowflake/api/storage.py))**: Saves the results into MongoDB.
6.  **Response**: Sends the full JSON (analyzed data) and your **Session Token** back to you.

---
