from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, SessionLocal
from .models import Employee
import logging
import os
import json
import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
# logging added

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = 60

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)


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
    try:
        redis_client.delete(f"employee:{employee_id}")

        logger.info(
            "Redis cache invalidated: employee_id=%s",
            employee_id
        )

    except redis.RedisError as exc:
         logger.warning(
            "Could not invalidate employee cache: %s",
            exc
        )

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
    cache_key = f"employee:{employee_id}"

    # Step 1: Check Redis cache
    try:
        cached_employee = redis_client.get(cache_key)

        if cached_employee:
            try:
                employee_data = json.loads(cached_employee)
                logger.info(
                    "Redis cache HIT: employee_id=%s",
                    employee_id
                )
                return employee_data

            except json.JSONDecodeError:
                logger.warning(
                    "Invalid cached data: employee_id=%s",
                    employee_id
                )
                redis_client.delete(cache_key)

    except redis.RedisError as exc:
        logger.warning(
            "Redis unavailable; falling back to PostgreSQL: %s",
            exc
        )

    # Step 2: Cache miss or Redis unavailable
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        logger.warning(
            "Employee not found: id=%s",
            employee_id
        )
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Step 3: Prepare employee data
    employee_data = {
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
        "department": employee.department,
        "designation": employee.designation,
        "salary": employee.salary
    }

    # Step 4: Store the result in Redis
    try:
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(employee_data)
        )

        logger.info(
            "Redis cache SET: employee_id=%s",
            employee_id
        )

    except (redis.RedisError, TypeError, ValueError) as exc:
        logger.warning(
            "Could not cache employee: %s",
            exc
        )

    return employee_data
    
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
    try:
        redis_client.delete(f"employee:{employee_id}")

        logger.info(
            "Redis cache invalidated: employee_id=%s",
            employee_id
        )

    except redis.RedisError as exc:
        logger.warning(
            "Could not invalidate employee cache: %s",
            exc
        )
    logger.info("Employee deleted: id=%s", employee_id)
    return {
        "message": "Employee deleted successfully"
    }
