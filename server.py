"""Development server entry point."""

import uvicorn

from app.config import load_env_file
from app.config import get_server_settings


def main() -> None:
    """Load local configuration and start Uvicorn."""

    load_env_file()
    settings = get_server_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
