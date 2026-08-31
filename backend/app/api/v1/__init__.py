"""
BMIM API v1 package.
"""
from fastapi import APIRouter

from app.api.v1 import auth, cpses, dashboard, mappings, matches, materials, national_materials, uploads, audit_logs, integration, system

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(cpses.router, prefix="/cpses", tags=["CPSEs"])
router.include_router(materials.router, prefix="/materials", tags=["Materials"])
router.include_router(matches.router, prefix="/matches", tags=["Matches"])
router.include_router(mappings.router, prefix="/mappings", tags=["Mappings"])
router.include_router(national_materials.router, prefix="/national-materials", tags=["National Materials"])
router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Trail"])
router.include_router(integration.router, prefix="/integration", tags=["SAP/ERP Integration"])
router.include_router(system.router, prefix="/system", tags=["System & AI Trace"])
