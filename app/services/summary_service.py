import os
import json
import google.generativeai as genai

from app.models.summary import JobSummary

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_summary(db, job_id, df):

    total_inr = df[df["currency"] == "INR"]["amount"].sum()

    total_usd = df[df["currency"] == "USD"]["amount"].sum()

    anomaly_count = int(df["is_anomaly"].sum())

    top_merchants = (
        df.groupby("merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
        .to_dict()
    )

    prompt = f"""
You are a financial analyst.

Return ONLY valid JSON.

{{
  "narrative":"...",
  "risk_level":"low"
}}

Information:

Total INR Spend:
{total_inr}

Total USD Spend:
{total_usd}

Anomaly Count:
{anomaly_count}

Top Merchants:
{top_merchants}
"""

    narrative = ""
    risk = "low"

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

        narrative = result["narrative"]

        risk = result["risk_level"]

    except Exception:

        narrative = (
            "Summary could not be generated."
        )

        risk = "unknown"

    summary = JobSummary(

        job_id=job_id,

        total_spend_inr=float(total_inr),

        total_spend_usd=float(total_usd),

        top_merchants=top_merchants,

        anomaly_count=anomaly_count,

        narrative=narrative,

        risk_level=risk,
    )

    db.add(summary)

    db.commit()