# MongoDB Atlas Setup & Integration Manual

This guide explains how to set up a MongoDB cluster and integrate it into the SnowAdvisor dashboard for storing Snowflake analytics reports.

---

## 🚀 1. Setup MongoDB Atlas (Cluster)

### Step 1: Create an Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
2. Sign up with Google or your email.

### Step 2: Create a Cluster
1. Log in and click **"Create"** to build a new cluster.
2. Select **"M0"** (Free tier).
3. Choose a provider (e.g., AWS) and a region near you.
4. Click **"Create Deployment"**.

### Step 3: Security & Access
1. **Database User**: Create a user with a password. **Keep this password safe!** Set the role to "Read and write to any database".
2. **Network Access**: Click "Network Access" in the sidebar. Click **"Add IP Address"**.
   - For local development, choose **"Allow Access from Anywhere"** (0.0.0.0/0) or "Add Current IP Address".
   - Click "Confirm".

### Step 4: Get Connection String
1. Go to your **"Database"** (Clusters) view.
2. Click the **"Connect"** button.
3. Select **"Drivers"** (Python).
4. Copy the connection string. It looks like this:
   `mongodb+srv://<db_user>:<db_password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`

---

## 🛠️ 2. Integration into SnowAdvisor

### Step 1: Add to [.env](file:///c:/Users/Abubakar/Desktop/snowflake/.env) File
Create a file named [.env](file:///c:/Users/Abubakar/Desktop/snowflake/.env) in the root folder of your project (the same folder where [app.py](file:///c:/Users/Abubakar/Desktop/snowflake/app.py) and [backend.py](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py) are located). I have already created a template for you at:
[c:\Users\Abubakar\Desktop\snowflake\.env](file:///c:/Users/Abubakar/Desktop/snowflake/.env)

Add your connection string there:

```bash
MONGODB_URI="mongodb+srv://<db_user>:<db_password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB="snowadvisor"
MONGODB_COLLECTION="reports"
```
*(Replace `<db_user>` and `<db_password>` with your created credentials)*

### Step 2: Python Code (backend.py)
Add the following code to [backend.py](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py) to enable MongoDB saving:

```python
import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def save_to_mongodb(data: dict):
    """Saves the intelligence report to MongoDB Atlas."""
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "snowadvisor")
    coll_name = os.getenv("MONGODB_COLLECTION", "reports")
    
    if not uri:
        print("MongoDB URI not found in environment variables.")
        return False
        
    try:
        client = pymongo.MongoClient(uri)
        db = client[db_name]
        collection = db[coll_name]
        
        # Add a timestamp if missing
        if "meta" not in data:
            data["meta"] = {"exported_at": datetime.now().isoformat()}
            
        result = collection.insert_one(data)
        print(f"Data saved to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"Failed to save to MongoDB: {e}")
        return False
```

### Step 3: Update [run_full_pipeline](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py#456-493)
Modify the end of your [run_full_pipeline](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py#456-493) function in [backend.py](file:///c:/Users/Abubakar/Desktop/snowflake/backend.py) to call the MongoDB function:

```python
# ... existing code ...
        fp, fn = save_json(result["account_info"], data)
        result["filepath"] = fp
        result["filename"] = fn
        
        # --- ADD THIS TO SAVE TO MONGODB ---
        save_to_mongodb(data)
        # -----------------------------------
        
        result["success"]  = True
# ... existing code ...
```

---

## 🏃 3. Run the Project
1. Install dependencies: `pip install pymongo python-dotenv`
2. Run the dashboard: `streamlit run app.py`
3. Enter your Snowflake credentials. After analysis, the data will be saved both as a local JSON and in your MongoDB cluster.
