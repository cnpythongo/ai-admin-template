from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.departments import router as department_router
from app.api.v1.menus import router as menu_router
from app.api.v1.operation_logs import router as operation_logs_router
from app.api.v1.permissions import router as permission_router
from app.api.v1.roles import router as role_router
from app.api.v1.system_configs import router as system_configs_router
from app.api.v1.users import router as users_router

router = APIRouter()

# Auth routes
router.include_router(auth_router)

# Department routes
router.include_router(department_router)

# Permission routes
router.include_router(permission_router)

# Menu routes
router.include_router(menu_router)

# Role routes
router.include_router(role_router)

# System config routes
router.include_router(system_configs_router)

# User routes
router.include_router(users_router)

# Operation log routes
router.include_router(operation_logs_router)
