from __future__ import annotations

import asyncio
import json
import os

from recal.adapters.strands_analyzer import StrandsOpportunityAnalyzer
from recal.application.ports import SearchResult
from recal.domain.entities import UserProfile


async def main() -> None:
    model_id = os.getenv(
        "BEDROCK_MODEL_ID",
        "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    region = os.getenv("AWS_REGION", "us-east-1")
    analyzer = StrandsOpportunityAnalyzer(
        model_id=model_id,
        region_name=region,
        max_tokens=1200,
    )
    results = [
        SearchResult(
            title="Recal AI Hackathon",
            url="https://example.com/recal-ai-hackathon",
            content=(
                "A fictional AI hackathon for students interested in Python, "
                "agents and cloud applications. Applications close on 2030-06-30."
            ),
        )
    ]
    profile = UserProfile(
        interests=["AI agents", "Python"],
        countries=["France"],
        study_level="university",
        skills=["Python", "cloud"],
        relevance_threshold=70,
    )
    opportunities = await analyzer.analyze(results, profile)
    print(json.dumps([op.__dict__ for op in opportunities], default=str, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
