"""Backward-compatible imports for the former monolithic module."""

from atez_collector.supporting import fetch_supporting_sources
from atez_collector.supporting.resmi_gazete_ozeti import parse_rg_ozeti
from atez_collector.supporting.tariff import normalize_tariff_notice

__all__ = ["fetch_supporting_sources", "normalize_tariff_notice", "parse_rg_ozeti"]
