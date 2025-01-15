import os
from typing import List, Dict
from utils import Dataset

import numpy as np
import pandas as pd
import scipy
import scipy as sp

# parameters for Welch's method for estimating power spectrum
NPERSEG = 60                    # length of segment
NOVERLAP = int(0.75 * NPERSEG)  # overlap of segments
NFFT = NPERSEG                  # length of FFT
WINDOW = "hann"                 # window function type

# parameters for saving data
PROCESSED_DATA_DIR = "processed_data"
DEPRESJON_PREFIX = "manual_depresjon"
PSYKOSE_PREFIX = "manual_psykose"
HYPERAKTIV_PREFIX = "manual_hyperaktiv"
MAIN_RESULTS_DIR = "results"

# helper functions
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


def get_day_part(df: pd.DataFrame, part: str) -> pd.DataFrame:
    """
    For given DataFrame with "timestamp" column returns only those rows that
    correspond to the chosen part of day.

    Parts are "day" and "night", defined as:
    - "day": [8:00, 21:00)
    - "night": [21:00, 8:00)

    :param df: DataFrame to select rows from
    :param part: part of day, either "day" or "night"
    :returns: DataFrame, subset of rows of df
    """
    if part == "day":
        df = df.loc[(df["timestamp"].dt.hour >= DAY_NIGHT_HOURS[0]) &
                    (df["timestamp"].dt.hour < DAY_NIGHT_HOURS[1])]
    elif part == "night":
        df = df.loc[(df["timestamp"].dt.hour >= DAY_NIGHT_HOURS[1]) |
                    (df["timestamp"].dt.hour < DAY_NIGHT_HOURS[0])]
    else:
        raise ValueError(f'Part should be "day" or "night", got "{part}"')

    return df


def fill_missing_activity(df: pd.DataFrame, freq: str = "min") -> pd.DataFrame:
    """
    Fill missing activity values by resampling based on given frequency.

    :param df: DataFrame with 'timestamp' and 'activity' columns.
    :param freq: Resampling frequency (default: minute).
    :return: DataFrame with missing values filled.
    """
    df = df.copy()  # create copy to avoid side effects

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df.set_index("timestamp", inplace=True)

    # resample to the basic frequency, i.e. minute; this will create NaNs for
    # any rows that may be missing
    df = df.resample(freq).mean()

    # recreate index and "timestamp" column
    df.reset_index(inplace=True)

    # fill any NaNs with mean activity value
    df["activity"] = df["activity"].fillna(df["activity"].mean())

    return df


def resample(df: pd.DataFrame, freq: str = "H") -> pd.DataFrame:
    """
    Resamples time series DataFrame with given frequency, aggregating each
    segment with a mean.

    :param df: DataFrame with "timestamp" and "activity" columns
    :param freq: resampling frequency passed to Pandas resample() function
    :returns: DataFrame with "timestamp" and "activity" columns
    """
    df = df.copy()  # create copy to avoid side effects

    # group with given frequency
    df = df.resample(freq, on="timestamp").mean()

    # recreate "timestamp" column
    df = df.reset_index()

    return df


def proportion_of_zeros(x: np.ndarray) -> float:
    """
    Calculates proportion of zeros in given array, i.e. number of zeros divided
    by length of array.

    :param x: 1D Numpy array
    :returns: proportion of zeros
    """
    # we may be dealing with floating numbers, we can't use direct comparison
    zeros_count = np.sum(np.isclose(x, 0))
    return zeros_count / len(x)


def power_spectral_density(df: pd.DataFrame) -> np.ndarray:
    """
    Calculates power spectral density (PSD) from "activity" column of a
    DataFrame.

    :param df: DataFrame with "activity" column
    :returns: 1D Numpy array with power spectral density
    """

    activity = df["activity"].values
    nperseg = min(NPERSEG, len(activity))  # Ensure nperseg doesn't exceed data length
    noverlap = int(0.75 * nperseg)

    psd = scipy.signal.welch(
        x=activity,
        fs=(1 / 60),
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=NFFT,
        window=WINDOW,
        scaling="density"
    )[1]
    return psd


def spectral_flatness(df: pd.DataFrame) -> float:
    """
    Calculates spectral flatness of a signal, i.e. a geometric mean of the
    power spectrum divided by the arithmetic mean of the power spectrum.

    If some frequency bins in the power spectrum are close to zero, they are
    removed prior to calculation of spectral flatness to avoid calculation of
    log(0).

    :param df: DataFrame with "activity" column
    :returns: spectral flatness value
    """

    activity = df["activity"].values
    nperseg = min(NPERSEG, len(activity))  # Ensure nperseg doesn't exceed data length
    noverlap = int(0.75 * nperseg)

    power_spectrum = scipy.signal.welch(
        activity,
        fs=(1 / 60),
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=NFFT,
        window=WINDOW,
        scaling="spectrum"
    )[1]

    non_zeros_mask = ~np.isclose(power_spectrum, 0)
    power_spectrum = power_spectrum[non_zeros_mask]

    return scipy.stats.gmean(power_spectrum) / power_spectrum.mean()


def extract_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts features from activity signal in time domain.

    :param df_resampled: DataFrame with "activity" column
    :returns: DataFrame with a single row representing features
    """
    X = df["activity"].values

    features = {
        "minimum": np.min(X),
        "maximum": np.max(X),
        "mean": np.mean(X),
        "median": np.median(X),
        "variance": np.var(X, ddof=1),  # apply Bessel's correction
        "kurtosis": sp.stats.kurtosis(X),
        "skewness": sp.stats.skew(X),
        "coeff_of_var": sp.stats.variation(X),
        "iqr": sp.stats.iqr(X),
        "trimmed_mean": sp.stats.trim_mean(X, proportiontocut=0.1),
        "entropy": sp.stats.entropy(X, base=2),
        "proportion_of_zeros": proportion_of_zeros(X)
    }

    return pd.DataFrame([features])


def extract_frequency_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts features from activity signal in frequency domain, i.e. calculated
    from its Power Spectral Density (PSD).

    :param df: DataFrame with "activity" column
    :returns: DataFrame with a single row representing features
    """
    X = power_spectral_density(df)

    features = {
        "minimum": np.min(X),
        "maximum": np.max(X),
        "mean": np.mean(X),
        "median": np.median(X),
        "variance": np.var(X),
        "kurtosis": sp.stats.kurtosis(X),
        "skewness": sp.stats.skew(X),
        "coeff_of_var": sp.stats.variation(X),
        "iqr": sp.stats.iqr(X),
        "trimmed_mean": sp.stats.trim_mean(X, proportiontocut=0.1),
        "entropy": sp.stats.entropy(X, base=2),
        "spectral_flatness": spectral_flatness(df)
    }

    return pd.DataFrame([features])


def extract_features_for_dataframes(dfs: List[pd.DataFrame], freq: str = "H") \
        -> Dict[str, pd.DataFrame]:
    """
    Calculates time and frequency features for given DataFrames. Uses given
    frequency for resampling.

    Calculates features separately for:
    - full 24hs
    - days: [8:00, 21:00)
    - nights: [21:00, 8:00)

    :param dfs: list of DataFrames to extract features from; each one has to
    have "timestamp" and "activity" columns
    :param freq: resampling frequency
    :returns: dictionary with keys "full_24h", "day" and "night", corresponding
    to features from given parts of day
    """
    full_dfs = basic_data_cleaning(dfs)
    full_dfs = [fill_missing_activity(df) for df in full_dfs]
    full_dfs = [resample(df, freq=freq) for df in full_dfs]

    night_dfs = [get_day_part(df, part="night") for df in full_dfs]
    day_dfs = [get_day_part(df, part="day") for df in full_dfs]

    datasets = {}

    for part, list_of_dfs in [("full_24h", full_dfs), ("night", night_dfs),
                              ("day", day_dfs)]:
        features = []
        for df in list_of_dfs:
            time_features = extract_time_features(df)
            freq_features = extract_frequency_features(df)

            merged_features = pd.merge(
                time_features,
                freq_features,
                left_index=True,
                right_index=True,
                suffixes=["_time", "_freq"]
            )
            features.append(merged_features)

        datasets[part] = pd.concat(features)
        datasets[part].reset_index(drop=True, inplace=True)

    return datasets



# manual feature engineering
datasets_names = ['hyperaktiv', 'depresjon', 'psykose']

for hours in [(6, 22), (8, 21)]:
    DAY_NIGHT_HOURS = hours
    day_night_format = f'{hours[0]}_{hours[1]}'

    for dataset_name in datasets_names:
        # loading
        if dataset_name == 'hyperaktiv':
            dataset = Dataset(dirpath=os.path.join("data", dataset_name), sep=';')
        else:
            dataset = Dataset(dirpath=os.path.join("data", dataset_name), sep=',')
        condition = dataset.condition
        control = dataset.control

        for cond in condition:
            cond.columns = cond.columns.str.lower()

        for contr in control:
            contr.columns = contr.columns.str.lower()

        condition = basic_data_cleaning(condition)
        control = basic_data_cleaning(control)

        # count features metrics
        condition_parts_dfs = extract_features_for_dataframes(condition, freq="h")
        control_parts_dfs = extract_features_for_dataframes(control, freq="h")

        datasets = {}

        for part in ["full_24h", "night", "day"]:
            condition_df = condition_parts_dfs[part]
            control_df = control_parts_dfs[part]

            entire_df = pd.concat([condition_df, control_df], ignore_index=True)
            datasets[part] = entire_df

        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

        for part, df in datasets.items():
            filename = f"{HYPERAKTIV_PREFIX}_{day_night_format}_{part}.csv"
            filepath = os.path.join(PROCESSED_DATA_DIR, filename)
            df.to_csv(filepath, index=False)

        y = np.concatenate((np.ones(len(condition)), np.zeros(len(control))))
        y = pd.Series(y, dtype=int)

        filepath = os.path.join(PROCESSED_DATA_DIR, f"hyperaktiv_{day_night_format}_y.csv")
        y.to_csv(filepath, header=False, index=False)
