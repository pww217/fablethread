"""Server package — re-exports for backward compatibility."""

from .app import (
    app,
    main,
    config,
    SAVE_DIR,
    _validate_stats,
)

__all__ = ["app", "main", "config", "SAVE_DIR", "_validate_stats"]
