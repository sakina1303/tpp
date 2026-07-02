DOMESTIC = [
    "Swiggy",
    "Ola",
    "IRCTC"
]


def detect(df):

    df["is_anomaly"] = False
    df["anomaly_reason"] = ""

    medians = (
        df.groupby("account_id")["amount"]
        .median()
        .to_dict()
    )

    for i, row in df.iterrows():

        median = medians.get(row["account_id"], 0)

        if median and row["amount"] > median * 3:

            df.at[i, "is_anomaly"] = True
            df.at[i, "anomaly_reason"] = "High Amount"

        if (
            row["currency"] == "USD"
            and row["merchant"] in DOMESTIC
        ):

            df.at[i, "is_anomaly"] = True
            df.at[i, "anomaly_reason"] = "Domestic Merchant + USD"

    return df