import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, constr
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, func, text, select
from sqlalchemy.orm import declarative_base, class_mapper  # Aquí es donde debes importar class_mapper
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime

# Leer la URL de la base de datos desde la variable de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está definida")

# Configuración de SQLAlchemy
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Modelo de la tabla
class OTask(Base):
    __tablename__ = "otasks"
    id = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())  # Fecha de creación


class TaskCreate(BaseModel):
    description: constr(min_length=1, max_length=200)

class TaskResponse(BaseModel):
    id: str
    description: str
    completed: bool
    created_at: str 

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        """Método para convertir el resultado ORM de SQLAlchemy en un dict para Pydantic."""
        if isinstance(obj, dict):
            obj_dict = obj
        else:
            if hasattr(obj, '__dict__'):
                obj_dict = obj.__dict__
            else:
                obj_dict = {column.key: getattr(obj, column.key) for column in class_mapper(obj.__class__).columns}

        if isinstance(obj_dict.get("created_at"), datetime):
            obj_dict["created_at"] = obj_dict["created_at"].isoformat()  # Convierte a formato ISO 8601

        return cls(**obj_dict)

# Modelo para actualizar el estado de la tarea
class TaskUpdate(BaseModel):
    completed: bool

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por tus dominios específicos si es necesario
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados
)

async def get_db():
    async with SessionLocal() as session:
        yield session

# Obtener todas las tareas
@app.get("/tasks", response_model=list[TaskResponse])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    """Obtener todas las tareas, ordenadas por fecha de creación (created_at)."""
    result = await db.execute(select(OTask).order_by(OTask.created_at.desc()))
    tasks = result.scalars().all()

    # Convertir los resultados en objetos TaskResponse usando el ORM
    return [TaskResponse.from_orm(task) for task in tasks]

# Agregar una nueva tarea
@app.post("/tasks", response_model=TaskResponse)
async def add_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Agregar una nueva tarea."""
    new_task = OTask(
        id=str(uuid.uuid4()),
        description=task.description,
        completed=False,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return TaskResponse.from_orm(new_task)

# Actualizar el estado de "completed" de una tarea
@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_status(
    task_id: str, task_update: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """Actualizar el estado de completado de una tarea."""
    result = await db.execute(text("SELECT * FROM otasks WHERE id = :id"), {"id": task_id})
    task = result.fetchone()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    await db.execute(
        text("UPDATE otasks SET completed = :completed WHERE id = :id"),
        {"completed": task_update.completed, "id": task_id}
    )
    await db.commit()

    return TaskResponse(id=task.id, description=task.description, completed=task_update.completed, created_at=task.created_at.isoformat())

# Eliminar una tarea
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Eliminar una tarea por ID."""
    result = await db.execute(text("SELECT * FROM otasks WHERE id = :id"), {"id": task_id})
    task = result.fetchone()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    await db.execute(text("DELETE FROM otasks WHERE id = :id"), {"id": task_id})
    await db.commit()

    return {"message": "Tarea eliminada"}
