"""Backward-compatible command entrypoint."""

from atez_collector.cli import main
from atez_collector.http_client import request_with_log
from atez_collector.official.discovery import build_candidate_urls, parse_fihrist
from atez_collector.pipeline import run

__all__ = ["build_candidate_urls", "parse_fihrist", "request_with_log", "run"]


if __name__ == "__main__":
    raise SystemExit(main())
