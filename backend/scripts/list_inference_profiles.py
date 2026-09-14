from __future__ import annotations

import os

import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
TARGET_MODEL = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
)


def main() -> None:
    client = boto3.client("bedrock", region_name=REGION)
    paginator = client.get_paginator("list_inference_profiles")
    matches: list[dict[str, object]] = []

    for page in paginator.paginate():
        for profile in page.get("inferenceProfileSummaries", []):
            profile_id = str(profile.get("inferenceProfileId", ""))
            profile_arn = str(profile.get("inferenceProfileArn", ""))
            profile_name = str(profile.get("inferenceProfileName", ""))
            models = profile.get("models", [])
            models_text = str(models)
            item = {
                "id": profile_id,
                "arn": profile_arn,
                "name": profile_name,
                "status": profile.get("status"),
                "models": models,
            }
            print(item)
            if TARGET_MODEL in models_text or "haiku" in f"{profile_id} {profile_name}".lower():
                matches.append(item)

    print("--- MATCHES ---")
    for match in matches:
        print(match)


if __name__ == "__main__":
    main()
