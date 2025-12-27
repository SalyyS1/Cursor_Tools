"""
Service package for Windows background service and scheduled task integration
"""

from .rotation_service import RotationService
from .service_manager import ServiceManager
from .service_coordinator import ServiceCoordinator
from .scheduled_task import ScheduledTaskManager

__all__ = [
    "RotationService",
    "ServiceManager",
    "ServiceCoordinator",
    "ScheduledTaskManager",
]
