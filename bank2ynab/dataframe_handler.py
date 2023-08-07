from __future__ import annotations

import logging
from typing import Dict, List

import pandas as pd


class DataframeHandler:
    # TODO - integrate payee mapping in this class

    """
    use the details for a specified config to produce a cleaned dataframe
    matching a given specification
    """

    def __init__(self) -> None:
        self.df = pd.DataFrame()
        self.api_transaction_df = pd.DataFrame()
        self.empty = None
        self.output_df = pd.DataFrame()

    def output_csv(self, path: str) -> None:
        """
        Writes df to the specified filepath as a csv file

        :param path: path to write exported file to
        :type path: str
        """
        self.output_df.to_csv(path, index=False)

    def run(
        self,
        *,
        file_path: str,
        delim: str,
        header_rows: int,
        footer_rows: int,
        encod: str,
        input_columns: List[str],
        output_columns: List[str],
        api_columns: List[str],
        cd_flags: List[str],
        date_format: str,
        date_dedupe: bool,
        fill_memo: bool,
        currency_fix: float,
    ) -> None:
        """
        Complete handling of Dataframe creation & output.

        :param df: dataframe to be modified
        :param file_path: Path to CSV file
        :param delim: CSV separator
        :param header_rows: Number of header rows
        :param footer_rows: Number of footer rows
        :param encod: CSV file encoding
        :param input_columns: columns present in input data
        :param output_columns: desired columns to be present in output data
        :param api_columns: desired columns to be present in api data
        :param cd_flags: parameter to indicate inflow/outflow for a row
        :param date_format: string format for date
        :param date_dedupe: whether to fill in date with previous if blank
        :param fill_memo: switch whether to fill blank memo with payee data
        :param currency_fix: value to divide all currency amounts by
        """
        # read data from input file to dataframe
        self.df = pd.read_csv(
            file_path,
            delimiter=delim,
            skipinitialspace=True,  # skip space after delimiter
            names=[],  # don't set column headers initially
            skiprows=header_rows,  # skip header rows
            skipfooter=footer_rows,  # skip footer rows
            skip_blank_lines=True,  # skip blank lines
            encoding=encod,
            engine="python",
        )

        # modify dataframe to match desired output
        self.parse_data(
            input_columns=input_columns,
            output_columns=output_columns,
            api_columns=api_columns,
            cd_flags=cd_flags,
            date_format=date_format,
            date_dedupe=date_dedupe,
            fill_memo=fill_memo,
            currency_fix=currency_fix,
        )
        # check if dataframe is empty
        self.empty = self.df.empty
        # set final columns & order for output file
        self.output_df = self.df[output_columns]
        # set final columns & order for api output
        self.api_transaction_df = self.df[api_columns]

    def parse_data(
        self,
        *,
        input_columns: List[str],
        output_columns: List[str],
        api_columns: List[str],
        cd_flags: List[str],
        date_format: str,
        date_dedupe: bool,
        fill_memo: bool,
        currency_fix: float,
    ) -> None:
        """
        Convert each column of the dataframe to match ideal output data

        :param input_columns: columns present in input data
        :param output_columns: desired columns to be present in output data
        :param api_columns: desired columns to be present in api data
        :param cd_flags: parameter to indicate inflow/outflow for a row
        :param date_format: string format for date
        :param date_dedupe: whether to fill in date with previous if blank
        :param fill_memo: switch whether to fill blank memo with payee data
        :param currency_fix: value to divide all currency amounts by
        :return: modified dataframe matching provided configuration values
        """
        # set column names based on input column list
        self.df.columns = input_columns
        # debug to see what our df is like before transformation
        logging.debug("\nInitial DF\n%s", self.df.head())
        # merge duplicate input columns
        merge_duplicate_columns(self.df, input_columns)
        # add missing columns
        add_missing_columns(self.df, input_columns, output_columns + api_columns)
        # fix date format
        self.df["Date"] = fix_date(self.df["Date"], date_format)
        self.df["Date"] = fill_empty_dates(self.df["Date"], date_dedupe)
        # fix inflow/outflow string formatting
        self.df["Inflow"] = clean_monetary_values(self.df["Inflow"])
        self.df["Outflow"] = clean_monetary_values(self.df["Outflow"])
        # process Inflow/Outflow flags
        self.df = cd_flag_process(self.df, cd_flags)
        # fix amounts (convert negative inflows and outflows etc)
        self.df = fix_amount(self.df, currency_fix)
        # auto fill memo from payee if required
        if fill_memo:
            self.auto_memo()

        # auto fill payee from memo
        self.auto_payee()
        # fix strings
        self.df["Payee"] = clean_strings(self.df["Payee"])
        self.df["Memo"] = clean_strings(self.df["Memo"])
        # remove invalid rows
        self.remove_invalid_rows()
        # fill API-specific columns
        self.fill_api_columns()
        # remove invalid rows
        self.remove_invalid_rows()
        # display parsed line count
        logging.info("Parsed %s lines", self.df.shape[0])
        # view final dataframe
        logging.debug("\nFinal DF\n%s", self.df.head(10))

    def remove_invalid_rows(self) -> None:
        """
        Removes invalid rows from dataframe.
        An invalid row is one which does not have a date
        or one without an Inflow or Outflow value.

        """
        # filter out rows where Inflow and Outflow are both blank
        self.df.query("Inflow.notna() | Outflow.notna()", inplace=True)
        # filter rows with an invalid date
        self.df.query("Date.notna()", inplace=True)
        self.df.fillna(0, inplace=True)
        self.df.query("amount!=0", inplace=True)
        self.df.reset_index(inplace=True)

    def fill_api_columns(self) -> None:
        """
        Generate API-specific columns using data in dataframe.
        """
        self.df["account_id"] = ""
        self.df["date"] = self.df["Date"].astype(str)
        self.df["payee_name"] = self.df["Payee"].str.slice(0, 50)
        self.df["memo"] = self.df["Memo"].str.slice(0, 100)
        self.df["category"] = ""
        self.df["cleared"] = "cleared"
        self.df["payee_id"] = ""
        self.df["category_id"] = ""
        self.df["approved"] = False
        self.df["flag_color"] = ""

        # import_id format = YNAB:amount:ISO-date:occurrences
        # Maximum 36 characters ("YNAB" + ISO-date = 10 characters)
        self.df["import_id"] = self.df.agg(
            lambda x: f"YNAB:{x['amount']}:{x['date']}:", axis=1
        )
        # count every instance of import id & add a counter to id
        self.df["same_id_count"] = (
            self.df.groupby(["import_id"]).cumcount() + 1
        ).astype(str)
        self.df["import_id"] = self.df["import_id"] + self.df["same_id_count"]
        # move import_id to the end
        cols = list(self.df.columns.values)
        cols.pop(cols.index("import_id"))
        self.df = self.df[cols + ["import_id"]]

        # view dataframe
        logging.debug("\nAfter API column processing\n%s", self.df.head())

    def auto_payee(self) -> None:
        """
        If Payee is blank, fill with contents of Memo column

        :param df: dataframe to modify
        :return: modified dataframe
        """
        self.df["Payee"].fillna(self.df["Memo"], inplace=True)

    def auto_memo(self) -> None:
        """
        If memo is blank, fill with contents of payee column.

        :param df: dataframe to modify
        :param fill_memo: boolean to check
        :return: modified dataframe
        """
        self.df["Memo"].fillna(self.df["Payee"], inplace=True)


def read_csv(
    file_path: str,
    delim: str,
    header_rows: int,
    footer_rows: int,
    encod: str,
) -> pd.DataFrame:
    """
    Read a specified CSV file into a Dataframe.

    :param file_path: Path to CSV file
    :param delim: CSV separator
    :param header_rows: Number of header rows
    :param footer_rows: Number of footer rows
    :param encod: CSV file encoding
    :return: Dataframe read from CSV file
    """
    return pd.read_csv(
        file_path,
        delimiter=delim,
        skipinitialspace=True,  # skip space after delimiter
        names=[],  # don't set column headers initially
        skiprows=header_rows,  # skip header rows
        skipfooter=footer_rows,  # skip footer rows
        skip_blank_lines=True,  # skip blank lines
        encoding=encod,
        engine="python",
    )


def merge_duplicate_columns(df: pd.DataFrame, input_columns: List[str]) -> pd.DataFrame:
    """
    Merges columns specified more than once in the input_columns list.
    Note: converts values into strings before merging.

    :param df: dataframe to modify
    :param input_columns: the list of columns in the input file
    :return: modified dataframe
    """

    # create dictionary mapping column names to indices of duplicates
    cols_to_merge: Dict[str, List[int]] = {}
    for index, col in enumerate(input_columns):
        if col not in cols_to_merge:
            cols_to_merge[col] = []
        cols_to_merge[col] += [index]

    for key, key_cols in cols_to_merge.items():
        if len(key_cols) > 1:
            # change first column to string
            df.iloc[:, key_cols[0]] = df.iloc[:, key_cols[0]].astype(str) + " "
            # merge every duplicate column into the 1st instance
            # of the column name
            for dupe_count, key_col in enumerate(key_cols[1:]):
                # add string version of each column onto the first column
                df.iloc[:, key_cols[0]] += f"{df.iloc[:, key_col]} "
                # rename duplicate column
                df.columns.values[key_col] = f"{key} {dupe_count}"
            # remove excess spaces
            df[key] = df[key].str.replace("\\s{2,}", " ", regex=True).str.strip()

    logging.debug("\nAfter duplicate merge\n%s", df.head())

    return df


def add_missing_columns(
    df: pd.DataFrame, input_cols: List[str], output_cols: List[str]
) -> pd.DataFrame:
    """
    Adds any missing required columns to the Dataframe.

    :param df: dataframe to modify
    :param input_columns: the list of columns in the input file
    :param output_columns: the desired list of columns as output
    :return: modified dataframe
    """
    # compare input & output column lists to find missing columns
    missing_cols = list(set(output_cols).difference(input_cols))
    # add missing output columns
    for col in missing_cols:
        df.insert(loc=0, column=col, value="")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    logging.debug("\nAfter adding missing columns:\n%s", df.head())
    return df


def cd_flag_process(df: pd.DataFrame, cd_flags: List[str]) -> pd.DataFrame:
    """
    Fix columns where inflow/outflow is indicated by a flag
    in a separate column.
    The cd_flag list is in the form
    ["indicator column, outflow flag, inflow flag"]
    (the code does not use the indicator flag specified in the flag list,
    but instead the "CDFlag" column specified in Input Columns)

    :param df: dataframe to modify
    :type df: pd.DataFrame
    :param cd_flags: list of parameters for applying indicators
    :type cd_flags: list
    :return: modified dataframe
    :rtype: pd.DataFrame
    """
    if len(cd_flags) == 3:
        outflow_flag = cd_flags[2]
        # if this row is indicated to be outflow, make inflow negative
        df.loc[df["CDFlag"] == outflow_flag, ["Inflow"]] = -1 * df["Inflow"]
    return df


def fix_amount(df: pd.DataFrame, currency_fix: float) -> pd.DataFrame:
    """
    Fix currency string formatting.
    Convert currency values to floats.
    Convert negative inflows into outflows and vice versa.

    :param df: dataframe to modify
    :type df: pd.DataFrame
    :return: modified dataframe
    :rtype: pd.DataFrame
    """
    # negative inflow = outflow
    df.loc[df["Inflow"] < 0, ["Outflow"]] = df["Inflow"] * -1
    df.loc[df["Inflow"] < 0, ["Inflow"]] = 0

    # negative outflow = inflow
    df.loc[df["Outflow"] < 0, ["Inflow"]] = df["Outflow"] * -1
    df.loc[df["Outflow"] < 0, ["Outflow"]] = 0

    # currency conversion if multiplier specified
    df["Inflow"] = df["Inflow"] / currency_fix
    df["Outflow"] = df["Outflow"] / currency_fix

    # create amount column for API (in milliunits)
    df["amount"] = (1000 * (df["Inflow"] - df["Outflow"])).astype(int)
    return df


def clean_monetary_values(num_series: pd.Series) -> pd.Series:
    """
    Performs the following operations on a provided series of strings:
    - Convert "," to "."
    - Remove every instance of "." except last one
    - Remove any characters except digits, "-", and "."
    - Fill in null values with 0

    :param num_series: series of values to modify
    :return: modified series
    """
    # convert all commas to full stops
    num_series.replace({"\\,": "."}, regex=True, inplace=True)
    # remove all except last decimal point
    num_series.replace({"\\.(?=.*?\\.)": ""}, regex=True, inplace=True)
    # remove all non-digit characters
    num_series.replace(
        {
            "[^\\d\\.-]": "",
        },
        regex=True,
        inplace=True,
    )
    # fill in null values with 0
    return_series = num_series.fillna(value=0).astype(float)
    return return_series


def clean_strings(string_series: pd.Series) -> pd.Series:
    """
    Perform various cleaning operations on provided string series.

    :param string_series: string series to modify
    :type string_series: pd.Series
    :return: cleaned series
    :rtype: pd.Series
    """
    modified_string_series = string_series
    # convert string to title case
    modified_string_series = modified_string_series.str.title()
    # remove non-alphanumeric
    modified_string_series = modified_string_series.replace(
        "[^a-zA-Z0-9 ]", " ", regex=True
    )
    # remove newline characters
    modified_string_series = modified_string_series.str.replace("\n", " ", regex=True)
    # strip leading and trailing whitespace
    modified_string_series = modified_string_series.str.strip()
    # replace multiple spacing with single
    modified_string_series = modified_string_series.str.replace(" +", " ", regex=True)
    return modified_string_series


def fix_date(date_series: pd.Series, date_format: str) -> pd.Series:
    """
    If provided with an input date format,
    process the date column to the ISO format.
    Any non-parseable dates are returned as a NaT null value

    :param df: dataframe to modify
    :type df: Series
    :param date_format: date format codes according to 1989 C standard
    (https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)
    :type date_format: str
    :return: modified dataframe
    :rtype: Series
    """
    formatted_date_series = pd.to_datetime(
        date_series,
        format=date_format,
        infer_datetime_format=True,
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    logging.debug("\nFixed dates:\n%s", date_series.head())

    return formatted_date_series


def fill_empty_dates(date_series: pd.Series, fill_dates: bool) -> pd.Series:
    """
    Fill in empty dates with values from previous cells.

    :param date_series: data series to modify
    :param fill_dates: whether to fill in empty dates or not
    :return: modified data series
    """
    if fill_dates:
        date_series.replace(
            r"^\s*$", pd.NA, regex=True, inplace=True  # type:ignore
        )
        date_series.fillna(method="ffill", inplace=True)  # type:ignore

    return date_series


def combine_dfs(df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Concatenate a list of provided dataframes.

    :param df_list: list of dataframes to concatenate
    :type df_list: list[pd.DataFrame]
    :return: concatenated dataframe
    :rtype: pd.DataFrame
    """
    merged_df = pd.concat(df_list, ignore_index=True).drop_duplicates()
    return merged_df
