import os
import json
import time
import google.generativeai as genai

from app.models.summary import JobSummary

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_summary(db, job_id, df):

    total_inr = float(
        df[df["currency"] == "INR"]["amount"].sum()
    )

    total_usd = float(
        df[df["currency"] == "USD"]["amount"].sum()
    )

    anomaly_count = int(
        df["is_anomaly"].sum()
    )

    top_merchants = (
        df.groupby("merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
        .to_dict()
    )

    prompt = f"""
You are an expert financial analyst.

Analyze the transaction statistics below.

Return ONLY valid JSON.

Schema:

{{
    "narrative":"2-3 sentence executive summary.",
    "risk_level":"low"
}}

Rules:

- risk_level MUST be one of:
  low
  moderate
  high

- Mention:
    • Total INR spend
    • Total USD spend
    • Top merchants
    • Number of anomalies

Statistics

Total INR Spend:
{total_inr}

Total USD Spend:
{total_usd}

Anomaly Count:
{anomaly_count}

Top Merchants:
{json.dumps(top_merchants)}
"""

    narrative = ""
    risk = "low"

    retries = 3

    for attempt in range(retries):

        try:

            response = model.generate_content(prompt)

            text = response.text.strip()

            print("\n========== SUMMARY RAW ==========")
            print(text)
            print("=================================\n")

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            result = json.loads(text)

            narrative = result["narrative"]

            risk = result["risk_level"].lower()

            if risk not in ["low", "moderate", "high"]:
                risk = "moderate"

            break

        except Exception as e:

            print(f"Summary retry {attempt+1}/3")
            print(e)

            time.sleep(2)

    if narrative == "":

        narrative = (
            f"Total expenditure was INR {total_inr:,.2f} "
            f"and USD {total_usd:,.2f}. "
            f"The highest spending merchants were "
            f"{', '.join(top_merchants.keys())}. "
            f"{anomaly_count} anomalous transaction(s) were detected."
        )

        if anomaly_count >= 10:
            risk = "high"
        elif anomaly_count >= 5:
            risk = "moderate"
        else:
            risk = "low"

    summary = JobSummary(

        job_id=job_id,

        total_spend_inr=total_inr,

        total_spend_usd=total_usd,

        top_merchants=top_merchants,

        anomaly_count=anomaly_count,

        narrative=narrative,

        risk_level=risk

    )

    db.add(summary)

    db.commit()