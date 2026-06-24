from __future__ import annotations

import uvicorn

from app.config import settings


def main() -> None:
    """Entry point for running the application directly."""
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
