"""
BMIM Models package – import all models here so Alembic can detect them.
"""
from app.models.cpse import CPSE
from app.models.user import User, UserRole
from app.models.material_category import MaterialCategory
from app.models.material import Material, MaterialStatus
from app.models.material_attribute import MaterialAttribute
from app.models.material_embedding import MaterialEmbedding
from app.models.material_match import MaterialMatch, MatchType, MatchStatus
from app.models.national_material import NationalMaterial, NationalMaterialStatus
from app.models.material_mapping import MaterialMapping, MappingStatus
from app.models.audit_log import AuditLog
from app.models.upload_job import UploadJob, UploadStatus

__all__ = [
    "CPSE",
    "User",
    "UserRole",
    "MaterialCategory",
    "Material",
    "MaterialStatus",
    "MaterialAttribute",
    "MaterialEmbedding",
    "MaterialMatch",
    "MatchType",
    "MatchStatus",
    "NationalMaterial",
    "NationalMaterialStatus",
    "MaterialMapping",
    "MappingStatus",
    "AuditLog",
    "UploadJob",
    "UploadStatus",
]
