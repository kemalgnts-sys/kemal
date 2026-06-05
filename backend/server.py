from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random
import string
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str
    user_type: str  # "buyer" or "inspector"
    
class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    full_name: str
    phone: str
    user_type: str
    is_verified: bool = False
    created_at: str

class InspectorProfile(BaseModel):
    user_id: str
    id_verified: bool = False
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_miles: int = 50
    total_inspections: int = 0
    rating: float = 5.0
    earnings: float = 0.0

class InspectionPackage(BaseModel):
    name: str
    price: float
    description: str
    features: List[str]

class VehicleInfo(BaseModel):
    make: str
    model: str
    year: int
    vin: Optional[str] = None
    color: str
    mileage: Optional[int] = None

class SellerInfo(BaseModel):
    name: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    lat: float
    lng: float

class InspectionRequestCreate(BaseModel):
    vehicle: VehicleInfo
    seller: SellerInfo
    package_type: str  # "basic", "premium", "professional"
    tip_amount: float = 0.0
    preferred_date: Optional[str] = None
    notes: Optional[str] = None

class InspectionRequestResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    buyer_id: str
    buyer_name: str
    vehicle: dict
    seller: dict
    package_type: str
    package_price: float
    tip_amount: float
    total_amount: float
    security_code: str
    status: str  # "pending", "accepted", "in_progress", "completed", "cancelled"
    inspector_id: Optional[str] = None
    inspector_name: Optional[str] = None
    created_at: str
    accepted_at: Optional[str] = None
    completed_at: Optional[str] = None

class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: str
    data: Optional[dict] = None

class InspectionStep(BaseModel):
    step_name: str
    description: str
    required_photos: int
    completed: bool = False
    photos: List[str] = []
    notes: str = ""

class InspectionReportCreate(BaseModel):
    inspection_id: str
    steps: List[dict]
    overall_notes: str
    recommendation: str  # "buy", "caution", "avoid"

# ============== PACKAGES ==============
PACKAGES = {
    "basic": InspectionPackage(
        name="Basic",
        price=100.0,
        description="Essential exterior and interior check",
        features=["Exterior inspection", "Interior check", "Basic engine check", "Test drive", "15 photos"]
    ),
    "premium": InspectionPackage(
        name="Premium", 
        price=250.0,
        description="Comprehensive mechanical inspection",
        features=["All Basic features", "Detailed engine inspection", "Undercarriage check", "Fluid levels", "30 photos", "Video walkthrough"]
    ),
    "professional": InspectionPackage(
        name="Professional",
        price=300.0,
        description="Complete professional assessment",
        features=["All Premium features", "OBD-II diagnostic scan", "Frame inspection", "Paint depth analysis", "50+ photos", "Detailed written report", "Video call summary"]
    )
}

INSPECTION_STEPS = [
    {"step_name": "exterior_front", "description": "Front view - Hood, grille, headlights, bumper", "required_photos": 3},
    {"step_name": "exterior_sides", "description": "Both sides - Doors, panels, mirrors, wheels", "required_photos": 4},
    {"step_name": "exterior_rear", "description": "Rear view - Trunk, taillights, bumper", "required_photos": 3},
    {"step_name": "interior", "description": "Interior - Dashboard, seats, console, carpet", "required_photos": 5},
    {"step_name": "engine", "description": "Engine bay - Engine, fluids, belts, hoses", "required_photos": 4},
    {"step_name": "undercarriage", "description": "Undercarriage - Frame, suspension, exhaust", "required_photos": 3},
    {"step_name": "vin_verification", "description": "VIN plate and documentation", "required_photos": 2},
    {"step_name": "test_drive", "description": "Test drive notes and observations", "required_photos": 1}
]

def generate_security_code():
    return ''.join(random.choices(string.digits, k=6))

def strip_security_code(inspection: dict) -> dict:
    safe_inspection = dict(inspection)
    safe_inspection.pop("security_code", None)
    return safe_inspection

def sanitize_file_extension(filename: Optional[str]) -> str:
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    if not suffix or not suffix.isalnum() or len(suffix) > 10:
        return "jpg"
    return suffix

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password": user.password,  # In production, hash this!
        "full_name": user.full_name,
        "phone": user.phone,
        "user_type": user.user_type,
        "is_verified": False,
        "created_at": created_at
    }
    
    await db.users.insert_one(user_doc)
    
    # Create inspector profile if user is inspector
    if user.user_type == "inspector":
        inspector_profile = {
            "user_id": user_id,
            "id_verified": False,
            "location_lat": None,
            "location_lng": None,
            "radius_miles": 50,
            "total_inspections": 0,
            "rating": 5.0,
            "earnings": 0.0
        }
        await db.inspector_profiles.insert_one(inspector_profile)
    
    return UserResponse(
        id=user_id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        user_type=user.user_type,
        is_verified=False,
        created_at=created_at
    )

@api_router.post("/auth/login", response_model=UserResponse)
async def login_user(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        phone=user["phone"],
        user_type=user["user_type"],
        is_verified=user.get("is_verified", False),
        created_at=user["created_at"]
    )

# ============== PACKAGES ROUTES ==============

@api_router.get("/packages")
async def get_packages():
    return {k: v.model_dump() for k, v in PACKAGES.items()}

# ============== INSPECTION REQUEST ROUTES ==============

@api_router.post("/inspections", response_model=InspectionRequestResponse)
async def create_inspection_request(request: InspectionRequestCreate, buyer_id: str):
    buyer = await db.users.find_one({"id": buyer_id}, {"_id": 0})
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    package = PACKAGES.get(request.package_type)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package type")
    
    inspection_id = str(uuid.uuid4())
    security_code = generate_security_code()
    created_at = datetime.now(timezone.utc).isoformat()
    total_amount = package.price + request.tip_amount
    
    inspection_doc = {
        "id": inspection_id,
        "buyer_id": buyer_id,
        "buyer_name": buyer["full_name"],
        "vehicle": request.vehicle.model_dump(),
        "seller": request.seller.model_dump(),
        "package_type": request.package_type,
        "package_price": package.price,
        "tip_amount": request.tip_amount,
        "total_amount": total_amount,
        "security_code": security_code,
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": created_at,
        "accepted_at": None,
        "completed_at": None,
        "preferred_date": request.preferred_date,
        "notes": request.notes
    }
    
    await db.inspections.insert_one(inspection_doc)
    
    # Notify nearby inspectors
    seller_lat = request.seller.lat
    seller_lng = request.seller.lng
    
    inspectors = await db.inspector_profiles.find({
        "id_verified": True,
        "location_lat": {"$ne": None}
    }, {"_id": 0, "user_id": 1, "location_lat": 1, "location_lng": 1, "radius_miles": 1}).to_list(1000)
    
    for inspector in inspectors:
        # Simple distance calculation (in production, use proper geo query)
        if inspector.get("location_lat") and inspector.get("location_lng"):
            distance = ((inspector["location_lat"] - seller_lat)**2 + (inspector["location_lng"] - seller_lng)**2)**0.5 * 69  # rough miles
            if distance <= inspector.get("radius_miles", 50):
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": inspector["user_id"],
                    "title": "New Inspection Job Available!",
                    "message": f"{request.vehicle.year} {request.vehicle.make} {request.vehicle.model} in {request.seller.city}, {request.seller.state} - ${total_amount}",
                    "type": "new_job",
                    "read": False,
                    "created_at": created_at,
                    "data": {"inspection_id": inspection_id}
                }
                await db.notifications.insert_one(notification)
    
    return InspectionRequestResponse(**{k: v for k, v in inspection_doc.items() if k != "_id"})

@api_router.get("/inspections/buyer/{buyer_id}", response_model=List[InspectionRequestResponse])
async def get_buyer_inspections(buyer_id: str):
    inspections = await db.inspections.find({"buyer_id": buyer_id}, {"_id": 0}).to_list(100)
    return inspections

@api_router.get("/inspections/available")
async def get_available_inspections(inspector_lat: float = 41.8781, inspector_lng: float = -87.6298, radius: int = 50):
    inspections = await db.inspections.find({"status": "pending"}, {"_id": 0}).to_list(100)
    
    nearby = []
    for inspection in inspections:
        seller_lat = inspection["seller"]["lat"]
        seller_lng = inspection["seller"]["lng"]
        distance = ((seller_lat - inspector_lat)**2 + (seller_lng - inspector_lng)**2)**0.5 * 69
        if distance <= radius:
            safe_inspection = strip_security_code(inspection)
            safe_inspection["distance_miles"] = round(distance, 1)
            nearby.append(safe_inspection)
    
    return sorted(nearby, key=lambda x: x["distance_miles"])

@api_router.post("/inspections/{inspection_id}/accept")
async def accept_inspection(inspection_id: str, inspector_id: str):
    inspection = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    if inspection["status"] != "pending":
        raise HTTPException(status_code=400, detail="Inspection already accepted")
    
    inspector = await db.users.find_one({"id": inspector_id}, {"_id": 0})
    if not inspector:
        raise HTTPException(status_code=404, detail="Inspector not found")
    if inspector.get("user_type") != "inspector":
        raise HTTPException(status_code=403, detail="Only inspectors can accept inspection jobs")
    
    inspector_profile = await db.inspector_profiles.find_one({"user_id": inspector_id}, {"_id": 0})
    if not inspector_profile or not inspector_profile.get("id_verified"):
        raise HTTPException(status_code=403, detail="Inspector ID verification is required")
    
    accepted_at = datetime.now(timezone.utc).isoformat()
    
    update_result = await db.inspections.update_one(
        {"id": inspection_id, "status": "pending"},
        {"$set": {
            "status": "accepted",
            "inspector_id": inspector_id,
            "inspector_name": inspector["full_name"],
            "accepted_at": accepted_at
        }}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Inspection already accepted")
    
    # Notify buyer
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": inspection["buyer_id"],
        "title": "Inspector Assigned!",
        "message": f"{inspector['full_name']} has accepted your inspection request.",
        "type": "inspection_accepted",
        "read": False,
        "created_at": accepted_at,
        "data": {"inspection_id": inspection_id}
    }
    await db.notifications.insert_one(notification)
    
    updated = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    return updated

@api_router.post("/inspections/{inspection_id}/verify-code")
async def verify_security_code(inspection_id: str, code: str):
    inspection = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    if inspection["security_code"] != code:
        raise HTTPException(status_code=400, detail="Invalid security code")
    
    existing_progress = await db.inspection_progress.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if existing_progress:
        return {"message": "Code already verified, inspection in progress", "steps": existing_progress["steps"]}
    
    if inspection["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Inspection must be accepted before verification")
    
    update_result = await db.inspections.update_one(
        {"id": inspection_id, "status": "accepted"},
        {"$set": {"status": "in_progress"}}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Inspection is already in progress or completed")
    
    # Create inspection progress document with steps
    steps = [InspectionStep(
        step_name=step["step_name"],
        description=step["description"],
        required_photos=step["required_photos"]
    ).model_dump() for step in INSPECTION_STEPS]
    
    progress_doc = {
        "inspection_id": inspection_id,
        "steps": steps,
        "current_step": 0,
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    await db.inspection_progress.insert_one(progress_doc)
    
    return {"message": "Code verified, inspection started", "steps": INSPECTION_STEPS}

@api_router.get("/inspections/{inspection_id}/progress")
async def get_inspection_progress(inspection_id: str):
    progress = await db.inspection_progress.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress

@api_router.post("/inspections/{inspection_id}/upload-photo")
async def upload_inspection_photo(
    inspection_id: str,
    step_name: str = Form(...),
    file: UploadFile = File(...)
):
    progress = await db.inspection_progress.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    if not any(step["step_name"] == step_name for step in progress["steps"]):
        raise HTTPException(status_code=404, detail="Inspection step not found")
    
    # Save file
    file_ext = sanitize_file_extension(file.filename)
    filename = f"{inspection_id}_{step_name}_{uuid.uuid4()}.{file_ext}"
    file_path = UPLOADS_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    photo_url = f"/uploads/{filename}"
    
    # Update progress
    update_result = await db.inspection_progress.update_one(
        {"inspection_id": inspection_id, "steps.step_name": step_name},
        {"$push": {"steps.$.photos": photo_url}}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Inspection step not found")
    
    return {"photo_url": photo_url}

@api_router.post("/inspections/{inspection_id}/complete-step")
async def complete_step(inspection_id: str, step_name: str, notes: str = ""):
    progress = await db.inspection_progress.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    
    step_index = next((index for index, step in enumerate(progress["steps"]) if step["step_name"] == step_name), None)
    if step_index is None:
        raise HTTPException(status_code=404, detail="Inspection step not found")
    
    if progress["steps"][step_index].get("completed"):
        return {"message": "Step already completed"}
    
    update_result = await db.inspection_progress.update_one(
        {"inspection_id": inspection_id, "steps.step_name": step_name},
        {"$set": {"steps.$.completed": True, "steps.$.notes": notes}}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Inspection step not found")
    
    # Move to next step
    current = progress["current_step"]
    if current == step_index and current < len(INSPECTION_STEPS) - 1:
        await db.inspection_progress.update_one(
            {"inspection_id": inspection_id},
            {"$set": {"current_step": current + 1}}
        )
    
    return {"message": "Step completed"}

@api_router.post("/inspections/{inspection_id}/submit-report")
async def submit_report(inspection_id: str, report: InspectionReportCreate):
    inspection = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    existing_report = await db.reports.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if inspection["status"] == "completed" and existing_report:
        return {"message": "Report already submitted", "report_id": existing_report["id"]}
    
    if inspection["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Inspection must be in progress before submitting a report")
    if not inspection.get("inspector_id"):
        raise HTTPException(status_code=400, detail="Inspection has no assigned inspector")
    
    progress = await db.inspection_progress.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if not progress:
        raise HTTPException(status_code=400, detail="Inspection progress not found")
    if not all(step.get("completed") for step in progress["steps"]):
        raise HTTPException(status_code=400, detail="All inspection steps must be completed before submitting a report")
    
    completed_at = datetime.now(timezone.utc).isoformat()
    
    update_result = await db.inspections.update_one(
        {"id": inspection_id, "status": "in_progress"},
        {"$set": {"status": "completed", "completed_at": completed_at}}
    )
    if update_result.modified_count == 0:
        existing_report = await db.reports.find_one({"inspection_id": inspection_id}, {"_id": 0})
        if existing_report:
            return {"message": "Report already submitted", "report_id": existing_report["id"]}
        raise HTTPException(status_code=400, detail="Inspection is already being submitted or completed")
    
    # Create report document
    report_doc = {
        "id": str(uuid.uuid4()),
        "inspection_id": inspection_id,
        "inspector_id": inspection["inspector_id"],
        "buyer_id": inspection["buyer_id"],
        "vehicle": inspection["vehicle"],
        "steps": report.steps,
        "overall_notes": report.overall_notes,
        "recommendation": report.recommendation,
        "created_at": completed_at
    }
    await db.reports.insert_one(report_doc)
    
    # Update inspector stats
    await db.inspector_profiles.update_one(
        {"user_id": inspection["inspector_id"]},
        {
            "$inc": {
                "total_inspections": 1,
                "earnings": inspection["total_amount"] * 0.8  # 80% to inspector
            }
        }
    )
    
    # Notify buyer
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": inspection["buyer_id"],
        "title": "Inspection Complete!",
        "message": f"Your inspection report for {inspection['vehicle']['year']} {inspection['vehicle']['make']} {inspection['vehicle']['model']} is ready.",
        "type": "report_ready",
        "read": False,
        "created_at": completed_at,
        "data": {"inspection_id": inspection_id, "report_id": report_doc["id"]}
    }
    await db.notifications.insert_one(notification)
    
    return {"message": "Report submitted successfully", "report_id": report_doc["id"]}

@api_router.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@api_router.get("/reports/inspection/{inspection_id}")
async def get_report_by_inspection(inspection_id: str):
    report = await db.reports.find_one({"inspection_id": inspection_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# ============== NOTIFICATIONS ==============

@api_router.get("/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_notifications(user_id: str):
    notifications = await db.notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

# ============== INSPECTOR PROFILE ==============

@api_router.get("/inspector/profile/{user_id}")
async def get_inspector_profile(user_id: str):
    profile = await db.inspector_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@api_router.put("/inspector/profile/{user_id}")
async def update_inspector_profile(user_id: str, location_lat: float, location_lng: float, radius_miles: int = 50):
    await db.inspector_profiles.update_one(
        {"user_id": user_id},
        {"$set": {
            "location_lat": location_lat,
            "location_lng": location_lng,
            "radius_miles": radius_miles
        }}
    )
    return {"message": "Profile updated"}

@api_router.post("/inspector/verify-id/{user_id}")
async def verify_inspector_id(user_id: str):
    # Mock ID verification - in production, integrate with ID verification service
    await db.inspector_profiles.update_one(
        {"user_id": user_id},
        {"$set": {"id_verified": True}}
    )
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_verified": True}}
    )
    return {"message": "ID verified successfully"}

@api_router.get("/inspector/jobs/{inspector_id}")
async def get_inspector_jobs(inspector_id: str):
    jobs = await db.inspections.find(
        {"inspector_id": inspector_id},
        {"_id": 0}
    ).to_list(100)
    return jobs

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "AutoCheck API is running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
