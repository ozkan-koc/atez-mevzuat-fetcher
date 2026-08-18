from pathlib import Path

ARTIFACT_VERSION = "atez-collector/v1"
SCHEMA_VERSION = "1.0"
ISTANBUL_TIMEZONE = "Europe/Istanbul"
OFFICIAL_BASE_URL = "https://www.resmigazete.gov.tr"
OFFICIAL_HOSTS = frozenset({"www.resmigazete.gov.tr", "resmigazete.gov.tr"})
OUTPUT_ROOT = Path("out")
REQUEST_TIMEOUT_SECONDS = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ATEZ-Mevzuat-Radari/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
