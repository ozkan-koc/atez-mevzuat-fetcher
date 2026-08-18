import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import ISTANBUL_TIMEZONE
from .pipeline import run


def default_target_date() -> str:
    return datetime.now(ZoneInfo(ISTANBUL_TIMEZONE)).strftime("%Y-%m-%d")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ATEZ Resmî Gazete evidence collector")
    parser.add_argument("date", nargs="?", default=default_target_date(), help="YYYY-MM-DD")
    args = parser.parse_args(argv)
    return run(args.date)
