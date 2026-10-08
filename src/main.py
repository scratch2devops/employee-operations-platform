from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, SessionLocal
from .models import Employee
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=engine)

from .config import APP_NAME
app = FastAPI(title="APP_NAME")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    designation: str
    salary: float

class EmployeeUpdate(BaseModel):
    name: str
    email: str
    department: str
    designation: str
    salary: float

@app.put("/employees/{employee_id}")
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    existing_employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if existing_employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    existing_employee.name = employee.name
    existing_employee.email = employee.email
    existing_employee.department = employee.department
    existing_employee.designation = employee.designation
    existing_employee.salary = employee.salary

    db.commit()
    db.refresh(existing_employee)
    logger.info("Employee updated: id=%s", employee_id)
    return existing_employee

@app.post("/employees")
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    new_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
        designation=employee.designation,
        salary=employee.salary
    )
    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)

    except IntegrityError:
        db.rollback()

        logger.warning("Employee creation failed: email already exists: %s",
            employee.email)
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    logger.info(
        "Employee created: id=%s name=%s",
        new_employee.id,
        new_employee.name
    )
        

    return new_employee

@app.get("/health")
def health():
    return {"status":"healthy"}

@app.get("/employees")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()

    logger.info("Retrieved %s employees", len(employees))

    return employees

@app.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
     employee = db.query(Employee).filter(Employee.id == employee_id).first()
     if employee is None:
        logger.warning("Employee rnot found: id=%s", employee_id)
        raise HTTPException(status_code=404, detail="Employee not found")
     logger.info("Employee retrieved: id=%s", employee_id)
     return employee
    
@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    db.delete(employee)
    db.commit()
    logger.info("Employee deleted: id=%s", employee_id)
    return {
        "message": "Employee deleted successfully"
    }