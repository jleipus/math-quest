import json
from pathlib import Path

from backend.main import app

# Written into the web app so openapi-typescript can consume it locally.
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote OpenAPI schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
