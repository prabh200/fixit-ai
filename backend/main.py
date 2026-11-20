# import os
# import uuid
# import sqlite3
# import tempfile
# from pathlib import Path
# from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from PIL import Image
# from models import RepairRequest
# from agent import diagnose
# from memory import remember_repair, recall_repairs
# from tools import estimate_cost, provider_search_links

# load_dotenv(Path(__file__).parent / ".env")
# app = FastAPI(title="FixIt AI", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# DB = Path(__file__).parent / "fixit.db"

# def init_db():
#     conn = sqlite3.connect(DB)
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS repair_requests (
#             id TEXT PRIMARY KEY,
#             customer_name TEXT,
#             location TEXT,
#             category TEXT,
#             problem_summary TEXT,
#             diagnosis_id TEXT,
#             preferred_contact TEXT,
#             status TEXT DEFAULT 'prepared',
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# @app.get("/health")
# def health():
#     return {"status": "ok", "app": "FixIt AI"}

# @app.post("/diagnose")
# async def diagnose_endpoint(
#     appliance_or_area: str = Form(...),
#     category: str = Form(...),
#     description: str = Form(...),
#     location: str = Form(""),
#     image: UploadFile | None = File(None)
# ):
#     image_path = None
#     try:
#         if image:
#             if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
#                 raise HTTPException(400, "Upload a JPG, PNG, or WEBP image.")
#             content = await image.read()
#             max_bytes = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
#             if len(content) > max_bytes:
#                 raise HTTPException(413, f"Image must be smaller than {max_bytes // (1024*1024)} MB.")
#             suffix = ".jpg" if image.content_type == "image/jpeg" else ".png"
#             with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
#                 temp.write(content)
#                 image_path = temp.name
#             try:
#                 with Image.open(image_path) as im:
#                     im.verify()
#             except Exception:
#                 raise HTTPException(400, "The uploaded file is not a valid image.")

#         result = diagnose(appliance_or_area, category, description, image_path)
#         diagnosis_id = str(uuid.uuid4())
#         data = result.model_dump()
#         memory_status = await remember_repair(
#             category, appliance_or_area, description, data
#         )
#         return {
#             "diagnosis_id": diagnosis_id,
#             "diagnosis": data,
#             "cost_estimate": estimate_cost(category),
#             "provider_search": provider_search_links(category, location) if location else [],
#             "memory_status": memory_status
#         }
#     except HTTPException:
#         raise
#     except Exception as exc:
#         raise HTTPException(
#             500,
#             f"Diagnosis failed. Check that Ollama is running and the selected model is installed. Details: {str(exc)[:300]}"
#         )
#     finally:
#         if image_path and os.path.exists(image_path):
#             os.remove(image_path)

# @app.get("/memory")
# async def memory_endpoint(q: str):
#     return await recall_repairs(q)

# @app.post("/repair-request")
# def create_repair_request(request: RepairRequest):
#     request_id = str(uuid.uuid4())
#     conn = sqlite3.connect(DB)
#     conn.execute("""
#         INSERT INTO repair_requests
#         (id, customer_name, location, category, problem_summary, diagnosis_id, preferred_contact)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#     """, (
#         request_id, request.customer_name, request.location, request.category,
#         request.problem_summary, request.diagnosis_id, request.preferred_contact
#     ))
#     conn.commit()
#     conn.close()
#     return {
#         "request_id": request_id,
#         "status": "prepared",
#         "message": "Your repair request has been saved locally. No provider has been contacted or appointment booked."
#     }

# @app.get("/repair-requests")
# def list_repair_requests():
#     conn = sqlite3.connect(DB)
#     conn.row_factory = sqlite3.Row
#     rows = conn.execute("SELECT * FROM repair_requests ORDER BY created_at DESC").fetchall()
#     conn.close()
#     return [dict(row) for row in rows]






import os
import uuid
import sqlite3
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from PIL import Image
from models import RepairRequest
from agent import diagnose
from memory import remember_repair, recall_repairs
from tools import estimate_cost, provider_search_links, find_nearby_providers, find_diy_videos

load_dotenv(Path(__file__).parent / ".env")
app = FastAPI(title="FixIt AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = Path(__file__).parent / "fixit.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repair_requests (
            id TEXT PRIMARY KEY,
            customer_name TEXT,
            location TEXT,
            category TEXT,
            problem_summary TEXT,
            diagnosis_id TEXT,
            preferred_contact TEXT,
            selected_provider TEXT,
            status TEXT DEFAULT 'prepared',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(repair_requests)").fetchall()]
    if "selected_provider" not in cols:
        conn.execute("ALTER TABLE repair_requests ADD COLUMN selected_provider TEXT")
    conn.commit()
    conn.close()

init_db()

@app.get("/health")
def health():
    return {"status": "ok", "app": "FixIt AI"}

@app.post("/diagnose")
async def diagnose_endpoint(
    appliance_or_area: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    location: str = Form(""),
    image: UploadFile | None = File(None)
):
    image_path = None
    try:
        if image:
            if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise HTTPException(400, "Upload a JPG, PNG, or WEBP image.")
            content = await image.read()
            max_bytes = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
            if len(content) > max_bytes:
                raise HTTPException(413, f"Image must be smaller than {max_bytes // (1024*1024)} MB.")
            suffix = ".jpg" if image.content_type == "image/jpeg" else ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(content)
                image_path = temp.name
            try:
                with Image.open(image_path) as im:
                    im.verify()
            except Exception:
                raise HTTPException(400, "The uploaded file is not a valid image.")

        result = diagnose(appliance_or_area, category, description, image_path)
        diagnosis_id = str(uuid.uuid4())
        data = result.model_dump()
        memory_status = await remember_repair(
            category, appliance_or_area, description, data
        )
        nearby = find_nearby_providers(appliance_or_area, category, location) if location else []
        diy_videos = (
            find_diy_videos(appliance_or_area, data.get("problem_summary", description))
            if data.get("safety_level") != "Emergency"
            else {"search_url": "", "videos": []}
        )
        return {
            "diagnosis_id": diagnosis_id,
            "diagnosis": data,
            "cost_estimate": estimate_cost(category),
            "nearby_providers": nearby,
            "provider_search": provider_search_links(appliance_or_area, category, location) if location else [],
            "diy_videos": diy_videos,
            "memory_status": memory_status
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            500,
            f"Diagnosis failed. Check that Ollama is running and the selected model is installed. Details: {str(exc)[:300]}"
        )
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

@app.get("/memory")
async def memory_endpoint(q: str):
    return await recall_repairs(q)

@app.post("/repair-request")
def create_repair_request(request: RepairRequest):
    request_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO repair_requests
        (id, customer_name, location, category, problem_summary, diagnosis_id, preferred_contact, selected_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request_id, request.customer_name, request.location, request.category,
        request.problem_summary, request.diagnosis_id, request.preferred_contact,
        request.selected_provider
    ))
    conn.commit()
    conn.close()
    return {
        "request_id": request_id,
        "selected_provider": request.selected_provider,
        "status": "prepared",
        "message": "Your repair request has been saved locally. No provider has been contacted or appointment booked."
    }

@app.get("/repair-requests")
def list_repair_requests():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM repair_requests ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]