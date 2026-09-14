from __future__ import annotations

import os

import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
)


def main() -> None:
    client = boto3.client("bedrock-runtime", region_name=REGION)
    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": "Réponds exactement : Recal Bedrock OK",
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 32,
            "temperature": 0,
        },
    )
    text = response["output"]["message"]["content"][0]["text"]
    print(f"region={REGION}")
    print(f"model_id={MODEL_ID}")
    print(f"response={text}")
    print(f"stop_reason={response.get('stopReason')}")


if __name__ == "__main__":
    main()
