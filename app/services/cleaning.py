import pandas as pd


def clean_dataframe(df: pd.DataFrame):

    df.columns = [c.strip().lower() for c in df.columns]

    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True,
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    df["currency"] = df["currency"].str.upper()

    df["status"] = df["status"].str.upper()

    df["category"] = df["category"].fillna("Uncategorised")

    df = df.drop_duplicates()

    return df