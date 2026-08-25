from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all BMIM models."""
    pass
