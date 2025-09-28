"""
Orchesity IDE OSS CLI
Command-line interface for Orchesity IDE OSS
"""

import argparse
import sys
import uvicorn
from pathlib import Path

# Add the project root to path (parent of src directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Orchesity IDE OSS - Multi-LLM Orchestration IDE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchesity-cli serve          # Start the web server
  orchesity-cli serve --port 8080  # Start on custom port
  orchesity-cli --help         # Show this help
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Orchesity IDE OSS {settings.app_version}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the web server")
    serve_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == "serve":
        print(f"🚀 Starting Orchesity IDE OSS v{settings.app_version}")
        print(f"📡 Server will be available at http://{args.host}:{args.port}")
        print(f"📚 API documentation at http://{args.host}:{args.port}/docs")

        uvicorn.run(
            "src.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
