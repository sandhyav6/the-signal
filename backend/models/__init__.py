# backend/models/__init__.py
from backend.models.models import (
    Base,
    User,
    Category,
    Article,
    Topic,
    ArticleTopic,
    UserPreference,
    UserInteraction,
    Bookmark,
)

__all__ = [
    "Base",
    "User",
    "Category",
    "Article",
    "Topic",
    "ArticleTopic",
    "UserPreference",
    "UserInteraction",
    "Bookmark",
]
