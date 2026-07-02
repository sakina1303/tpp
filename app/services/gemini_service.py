import os
import json
import time
import pandas as pd
import google.generativeai as genai

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def classify_transactions_batch(df):

    all_categories = {}

    batch_size = 20

    for start in range(0, len(df), batch_size):

        batch = df.iloc[start:start + batch_size]

        prompt = """
You are a financial transaction classifier.

Classify EVERY transaction.

Return ONLY valid JSON.

Example:

[
 {"index":0,"category":"Shopping"},
 {"index":1,"category":"Food"}
]

Categories:

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

Transactions:

"""

        for local_index, (_, row) in enumerate(batch.iterrows()):

            prompt += f"""

Index: {local_index}

Merchant: {row['merchant']}

Notes: {row['notes']}

"""

        retries = 3

        for attempt in range(retries):

            try:

                response = model.generate_content(prompt)

                text = response.text.strip()

                if text.startswith("```"):
                    text = (
                        text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )

                result = json.loads(text)

                for item in result:

                    global_index = batch.index[item["index"]]

                    all_categories[global_index] = item["category"]

                break

            except Exception:

                print(f"Retry {attempt+1}")

                time.sleep(2)

    return all_categories