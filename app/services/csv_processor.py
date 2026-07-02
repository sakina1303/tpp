import pandas as pd

from app.services.cleaning import clean_dataframe
from app.services.anomaly_detector import detect


def process_csv(filepath):

    df = pd.read_csv(filepath)

    raw_rows = len(df)

    df = clean_dataframe(df)

    clean_rows = len(df)

    df = detect(df)

    return {
        "raw_rows": raw_rows,
        "clean_rows": clean_rows,
        "data": df
    }