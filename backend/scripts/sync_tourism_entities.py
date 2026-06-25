from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.tourism_regulation_service import TourismRegulationService


def main() -> None:
    service = TourismRegulationService()
    cache = service.sync_entities()
    print(
        "Synced "
        f"{len(cache.get('entities', []))} tourism entities "
        f"from {cache.get('source_url')} "
        f"at {cache.get('last_synced')}"
    )


if __name__ == "__main__":
    main()
