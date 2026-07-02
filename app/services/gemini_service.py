import os
import google.generativeai as genai

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def classify_transaction(merchant, notes):
    prompt = f"""
Classify this transaction into ONE category.

Merchant:
{merchant}

Notes:
{notes}

Return only one word.

Examples:
Shopping
Food
Travel
Recharge
Entertainment
Bills
Healthcare
Education
Others
"""

    try:

        response = model.generate_content(prompt)

        return response.text.strip()

    except Exception:

        return "Others"