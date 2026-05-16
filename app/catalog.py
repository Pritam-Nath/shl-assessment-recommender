import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.json"

TYPE_LABELS = {
    "A": "Ability & Aptitude",
    "B": "Biodata & Situational Judgement",
    "C": "Competencies",
    "D": "Development & 360",
    "E": "Assessment Exercises",
    "K": "Knowledge & Skills",
    "P": "Personality & Behavior",
    "S": "Simulations",
}


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return _fallback_catalog()
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        items = json.load(f)
    return [item for item in items if item.get("name") and item.get("url")]


def _fallback_catalog() -> list[dict[str, Any]]:
    base = "https://www.shl.com/products/product-catalog/view/"
    return [
        {
            "name": "Java 8 (New)",
            "url": base + "java-8-new/",
            "test_type": "K",
            "description": "Measures Java class design, exceptions, generics, collections, concurrency, JDBC and Java I/O fundamentals.",
            "job_levels": "Mid-Professional, Professional Individual Contributor",
            "languages": "English (USA)",
            "duration": "10",
            "remote_testing": True,
            "adaptive_irt": False,
        },
        {
            "name": "Programming Concepts",
            "url": base + "programming-concepts/",
            "test_type": "K",
            "description": "Measures core computer science programming concepts across languages, including algorithms, data types, program flow and structure.",
            "job_levels": "Mid-Professional, Professional Individual Contributor",
            "languages": "English (USA)",
            "duration": "25",
            "remote_testing": True,
            "adaptive_irt": False,
        },
        {
            "name": "Occupational Personality Questionnaire OPQ32r",
            "url": base + "occupational-personality-questionnaire-opq32r/",
            "test_type": "P",
            "description": "Personality and behavior questionnaire for workplace preferences and behavioral style.",
            "job_levels": "All",
            "languages": "English (USA)",
            "duration": "25",
            "remote_testing": True,
            "adaptive_irt": False,
        },
    ]
