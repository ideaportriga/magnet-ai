#!/usr/bin/env python3
"""
Test script for creating an evaluation record
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.db.database import get_async_db
from services.evaluations.evaluations_service import EvaluationsService


async def test_evaluation_creation():
    """Test creating an evaluation record"""
    print("🧪 Testing creation of evaluation record...")

    # Data for creating evaluation
    evaluation_data = {
        "job_id": "test-job-123",
        "type": "agent_evaluation",
        "test_sets": [
            {
                "system_name": "MANUAL_TEST_SET",
                "id": "821e03d7-11b8-4ef4-9e7f-ec22e6d8a17d",
            }
        ],
        "started_at": datetime.now(timezone.utc),
        "status": "running",
        "errors": [],  # Correct type - list of strings
        "tool": {"type": "test_tool", "config": {}, "system_name": "TEST_TOOL"},
        "results": None,
    }

    try:
        # Get database connection
        async for db in get_async_db():
            # Create service
            evaluations_service = EvaluationsService(session=db)

            # Create record
            print(f"📝 Creating evaluation with data: {evaluation_data}")
            evaluation = await evaluations_service.create(evaluation_data)

            print(f"✅ Successfully created evaluation with ID: {evaluation.id}")
            print("📊 Evaluation data:")
            print(f"   - ID: {evaluation.id}")
            print(f"   - Job ID: {evaluation.job_id}")
            print(f"   - Type: {evaluation.type}")
            print(f"   - Status: {evaluation.status}")
            print(f"   - Test Sets: {evaluation.test_sets}")
            print(f"   - Started At: {evaluation.started_at}")
            print(f"   - Errors: {evaluation.errors}")
            print(f"   - Tool: {evaluation.tool}")

            return evaluation

    except Exception as e:
        print(f"❌ Error creating evaluation: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_evaluation_creation())
