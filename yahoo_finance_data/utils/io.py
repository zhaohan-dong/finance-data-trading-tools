import pandas as pd
import os
import datetime

def df_to_parquet(df: pd.DataFrame, root_dir: str, filepath: str=None, engine: str = "pyarrow", compression: str = "gzip") -> None:
    # If no filename is given, we'll store parquet files in a directory tree with individual ticker/date
    if filepath == None:
        dates = df["Datetime"].dt.date.unique()
        tickers = df["Ticker"].unique()
        for ticker in tickers:
            if not os.path.exists(os.path.join(root_dir, ticker)):
                os.makedirs(os.path.join(root_dir, ticker), exist_ok=False)
            for date in dates:
                write_df = df.loc[(df["Ticker"]==ticker) & (df["Datetime"].dt.date==date), :]
                write_df.to_parquet(path=os.path.join(root_dir, ticker, f"{ticker}-{date}.parquet"), engine=engine, compression=compression)
    else:
        df.to_parquet(path=filepath, engine=engine, compression=compression)

def read_parquet(root_dir: str=None, filepath: str=None, tickers: str=None, start: str=None, end: str=None, engine: str="pyarrow") -> pd.DataFrame:

    def get_files_within_date_range(directory_path, start=None, end=None) -> list[str]:
        filenames = [file for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file))]

        # Note: filenames in format ./saved_directory/AAPL/AAPL-2023-01-01.parquet
        # Need to get 2023-01-01 as datetime and filter all pathnames with that element
        if not start:
            start = min([datetime.datetime.strptime(filename.split('-', maxsplit=1)[1].split(".")[0], '%Y-%m-%d') for filename in filenames])
        else:
            start = datetime.datetime.strptime(start, '%Y-%m-%d')

        if not end:
            end = max([datetime.datetime.strptime(filename.split('-', maxsplit=1)[1].split(".")[0], '%Y-%m-%d') for filename in filenames])
        else:
            end = datetime.datetime.strptime(end, '%Y-%m-%d')

        files_within_date_range = [os.path.join(directory_path, filename) for filename in filenames
                                   if start <= datetime.datetime.strptime(filename.split('-', maxsplit=1)[1].split(".")[0], '%Y-%m-%d') <= end]
        return files_within_date_range

    output_df = pd.DataFrame()

    # Read tickers
    if not filepath and root_dir:
        if tickers==None:
            tickers = [ticker for ticker in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, ticker))]

        for ticker in tickers:
            # Get a list of filenames for the ticker within the given daterange
            files = get_files_within_date_range(directory_path=os.path.join(root_dir, ticker), start=start, end=end)

            # Join the files
            for file in files:
                output_df = pd.concat([output_df,
                                       pd.read_parquet(path=file,
                                                       engine=engine,
                                                       dtype_backend="pyarrow")])
    elif filepath and not root_dir:
        output_df = pd.read_parquet(path=filepath)
    else:
        print("Please provide either a root directory to saved files, or a filename to read.")

    return output_df