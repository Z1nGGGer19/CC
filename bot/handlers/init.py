from .base import router as base_router
from .campus import router as campus_router
from .dorm import router as dorm_router
from .events import router as events_router
from .rules import router as rules_router
from .search import router as search_router
from .settings import router as settings_router
from .support import router as support_router

__all__ = [
    'base_router',
    'campus_router',
    'dorm_router',
    'events_router',
    'rules_router',
    'search_router',
    'settings_router',
    'support_router'
]