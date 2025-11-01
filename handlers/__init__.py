"""
Handlers package
"""
from .commands import commands_router
from .photo_handler import photo_router
from .calendar import calendar_router

__all__ = ['commands_router', 'photo_router', 'calendar_router']
