# myproject_server/src/myproject_server/models/__init__.py
from .user import User

# This tells Ruff/Linters that these are exported and 'used'
__all__ = ["User"]
