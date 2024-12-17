# Backend de Tareas - FastAPI

Este es un backend simple para gestionar tareas, construido con **FastAPI**, **SQLAlchemy** y **PostgreSQL**. El proyecto proporciona un API RESTful para realizar operaciones CRUD sobre tareas (crear, leer, actualizar y eliminar), con soporte para operaciones asincrónicas.

## Requisitos

- Python 3.8 o superior
- PostgreSQL o cualquier otra base de datos compatible con SQLAlchemy
- Dependencias de Python:
  - `fastapi`
  - `sqlalchemy`
  - `psycopg2`
  - `pydantic`
  - `python-dotenv`
  - `uvicorn`
  
# Ejecucion del servidor 
Puedes ejecutar el servidor localmente utilizando uvicorn. En e directorio raíz del proyecto, ejecuta el siguiente comando:
uvicorn main:app --reload

Puedes instalar las dependencias ejecutando:

```bash
pip install -r requirements.txt

