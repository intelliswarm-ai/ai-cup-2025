"""
Employee Directory API Service
Provides employee contact information for email enrichment
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import json
import os

app = FastAPI(title="Employee Directory API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Employee(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    mobile: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

# Load employees from JSON file
DATA_DIR = "/app/data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_employees():
    if os.path.exists(EMPLOYEES_FILE):
        with open(EMPLOYEES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_employees(employees):
    with open(EMPLOYEES_FILE, 'w') as f:
        json.dump(employees, f, indent=2)

@app.get("/")
async def root():
    return {"service": "Employee Directory API", "status": "running"}

@app.get("/api/employees", response_model=List[Employee])
async def get_all_employees():
    """Get all employees"""
    employees = load_employees()
    return employees

@app.get("/api/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """Get employee by ID"""
    employees = load_employees()
    for emp in employees:
        if emp["employee_id"] == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

@app.get("/api/employees/by-email/{email}", response_model=Employee)
async def get_employee_by_email(email: str):
    """Get employee by email address"""
    employees = load_employees()
    email_lower = email.lower()
    for emp in employees:
        if emp["email"].lower() == email_lower:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

@app.get("/api/employees/search/{query}")
async def search_employees(query: str):
    """Search employees by name or email"""
    employees = load_employees()
    query_lower = query.lower()
    results = []

    for emp in employees:
        if (query_lower in emp["first_name"].lower() or
            query_lower in emp["last_name"].lower() or
            query_lower in emp["email"].lower()):
            results.append(emp)

    return results

@app.post("/api/employees", response_model=Employee)
async def create_employee(employee: Employee):
    """Create a new employee"""
    employees = load_employees()

    # Check if employee_id already exists
    for emp in employees:
        if emp["employee_id"] == employee.employee_id:
            raise HTTPException(status_code=400, detail="Employee ID already exists")

    employees.append(employee.dict())
    save_employees(employees)
    return employee

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    employee_count = len(load_employees())
    return {
        "status": "healthy",
        "employee_count": employee_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
