#!/usr/bin/env python3
"""Find prompt templates with null/empty text that cause null content errors."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from core.config.app import alchemy  # noqa: E402
from sqlalchemy import text  # noqa: E402


NULL_CONTENT_TEMPLATES = [
    "DEFAULT_AGENT_CLASSIFICATION_PASS",
    "EXTRACT_EMAILS",
    "GENERATE_OPENAPI_SCHEMA",
]


async def main():
    async with alchemy.get_session() as session:
        for name in NULL_CONTENT_TEMPLATES:
            r = await session.execute(
                text("""
                SELECT p.system_name,
                       v->>'text' as template_text,
                       v->>'variant' as variant_name
                FROM prompts p, jsonb_array_elements(p.variants) v
                WHERE p.system_name = :name
                LIMIT 3
            """),
                {"name": name},
            )
            rows = r.fetchall()
            for row in rows:
                txt = row.template_text
                print(
                    f"{name} [{row.variant_name}]: text={repr(txt[:100] if txt else txt)}"
                )


asyncio.run(main())
