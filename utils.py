import pandas as pd


class DuplicateException(Exception):
    def __init__(self, message, df):
        super().__init__(message)
        self.duplicate_df = df


columns = ["total", "taxes", "earnings"]


def create_salary_df(path):
    if path is not None:
        df = pd.read_excel(path, index_col=0)
    else:
        df = pd.DataFrame(columns=columns)
        df.index.name = "date"
    df = df[~df.index.duplicated(keep='first')]
    return df
