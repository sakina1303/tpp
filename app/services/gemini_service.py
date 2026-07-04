import os
import json
import time
import google.generativeai as genai

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def classify_transactions_batch(df):

    all_categories = {}
    failed_rows = set()

    batch_size = 20

    for start in range(0, len(df), batch_size):

        batch = df.iloc[start:start + batch_size]

        prompt = """
You are an expert financial transaction classifier.

Classify EVERY transaction.

Return ONLY valid JSON.

Example:

[
    {"index":0,"category":"Shopping"},
    {"index":1,"category":"Food"}
]

Allowed Categories:

Shopping
Food
Travel
Transport
Utilities
Cash Withdrawal
Entertainment
Healthcare
Education
Recharge
Bills
Others

DO NOT skip any transaction.

Transactions:
"""

        for local_index, (_, row) in enumerate(batch.iterrows()):

            prompt += f"""

Index: {local_index}
Merchant: {row['merchant']}
Notes: {row['notes']}
"""

        retries = 3
        success = False

        for attempt in range(retries):

            try:

                response = model.generate_content(prompt)

                print("\n================ GEMINI RAW RESPONSE ================\n")
                print(response.text)
                print("\n=====================================================\n")

                text = response.text.strip()

                if text.startswith("```"):
                    text = (
                        text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )

                result = json.loads(text)

                for idx in batch.index:
                    all_categories[idx] = "Others"

                for item in result:

                    local_idx = item["index"]

                    if local_idx < len(batch):

                        global_idx = batch.index[local_idx]

                        all_categories[global_idx] = item["category"]

                success = True
                break

            except Exception as e:

                print(f"\nRetry {attempt + 1}/3")
                print(e)

                # Exponential Backoff
                time.sleep(2 ** attempt)

        if not success:

            print("Gemini failed for this batch. Using Others.")

            for idx in batch.index:

                all_categories[idx] = "Others"
                failed_rows.add(idx)

    return {
        "categories": all_categories,
        "failed_rows": failed_rows
    }