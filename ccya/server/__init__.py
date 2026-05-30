"""Server package — re-exports for backward compatibility."""

from .app import (
    app,
    main,
    config,
)

__all__ = ["app", "main", "config"]
