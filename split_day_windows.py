import os
from typing import List

import numpy as np
import pandas as pd
from utils import Dataset

PROCESSED_DATA_DIR = "processed_data"


def basic_data_cleaning(data: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Assumes DataFrames with "timestamp", "date" and "activity" columns.

    Performs cleaning operations:
    - Format "timestamp" to YYYY-MM-DD HH:MM:SS
    - Drop redundant "date" column
    - Convert "activity" to float32

    :param data: list of DataFrames
    :returns: list of cleaned DataFrames
    """
    data = [df.copy() for df in data]  # create copy to avoid side effects

    for df in data:
        # Convert and enforce the desired timestamp format
        df["timestamp"] = pd.to_datetime(df["timestamp"], dayfirst=False)
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Drop "date" column if it exists
        if "date" in df.columns:
            df.drop("date", axis=1, inplace=True)

        # Ensure "activity" column is float32
        df["activity"] = df["activity"].astype(np.float32)
    return data


def split_ts_to_24h_series(data, window_size: int = 24):
    window_size = pd.Timedelta(hours=window_size)
    data_windows = []
    for series in data:
        series["timestamp"] = pd.to_datetime(series["timestamp"], dayfirst=False)
        windows = []

        start_time = series["timestamp"][0]
        end_time = start_time + window_size

        while end_time < series["timestamp"].max():
            window_data = series[(series['timestamp'] >= start_time) & (series['timestamp'] < end_time)]
            if len(window_data) == 1440:  # check if the window is full, 1440 samples for 24h
                windows.append(window_data)
            start_time = end_time
            end_time = start_time + window_size

        data_windows.append(windows)

    return data_windows


def save_windows(data_windows, dataset, patient_class='condition'):
    id = 0
    for windows in data_windows:
        id += 1
        path = f"{PROCESSED_DATA_DIR}/day_windows/{dataset}/{patient_class}/{id}"
        os.makedirs(path, exist_ok=True)
        window_id = 0
        for window in windows:
            window_id += 1
            filepath = os.path.join(PROCESSED_DATA_DIR, 'day_windows', dataset, patient_class, str(id),  f"window_{window_id}.csv")
            window.to_csv(filepath, header=True, index=False)


def split_day_windows():
    datasets = ['hyperaktiv', 'depresjon', 'psykose']
    for dataset_name in datasets:
        if dataset_name == 'hyperaktiv': sep = ';'
        else: sep = ','

        dataset = Dataset(dirpath=os.path.join("data", dataset_name), sep=sep)
        condition = dataset.condition
        control = dataset.control

        for cond in condition:
            cond.columns = cond.columns.str.lower()

        for contr in control:
            contr.columns = contr.columns.str.lower()

        condition = basic_data_cleaning(condition)
        control = basic_data_cleaning(control)

        data_windows = split_ts_to_24h_series(condition, window_size=24)
        save_windows(data_windows=data_windows, dataset=dataset_name, patient_class='condition')
        data_windows = split_ts_to_24h_series(control, window_size=24)
        save_windows(data_windows=data_windows, dataset=dataset_name, patient_class='control')

split_day_windows()