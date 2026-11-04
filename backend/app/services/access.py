"""Replaceable demo catalog and deny-by-default manager policy, not authentication."""
from dataclasses import dataclass
from ..demo_models import Role

# Verified Active corporate IDs, 2026-10-28. Illustrative application roles only.
PERSONAS: dict[int, Role] = \
    {60: 'manager',
     69: 'employee',
     1: 'hr_admin'
     }
ACTOR_STATUSES = ('Active',)
TARGET_STATUSES = ('Active', 'Leave')

class DemoError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message

@dataclass(frozen=True)
class Actor:
    employee_id: int
    role: Role

def require_manager(actor: Actor) -> None:
    if actor.role != 'manager':
        raise DemoError(403, 'demo_access_denied', 'Select a Manager persona to view direct reports.')

def unavailable() -> DemoError:
    return DemoError(404, 'employee_unavailable', 'Employee unavailable in the current report scope.')
