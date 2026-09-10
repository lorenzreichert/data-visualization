import pandas as pd
import streamlit as st

measures = ["Sum", "Count", "Unique", "Mean value", "Minimum", "25 %", "Median", "75 %", "Maximum", "Range",
            "Interquartile range / H-spread", "Modal value", "Modal value frequency", "Standard deviation",
            "Variance"]


# ---------------------------------------------------------
# Load data from file
# ---------------------------------------------------------
def load_data(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file), None

    elif uploaded_file.name.endswith(".xlsx"):
        excel_file = pd.ExcelFile(uploaded_file)
        sheets = excel_file.sheet_names
        selected_sheet = st.selectbox(
            "Select spreadsheet",
            sheets
        )

        data_frame = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        return data_frame, selected_sheet

    else:
        raise ValueError("File type not supported. File extension must be .csv or .xlsx")


# ---------------------------------------------------------
# Create data frame with measures
# ---------------------------------------------------------
def get_measures(data_frame):
    data_frame.describe(include="all")


def get_metric(data, metric):
    if metric not in measures:
        return None
    else:
        match metric:
            case "Sum":
                return data.sum()
            case "Count":
                return data.count()
            case "Unique":
                return data.nunique()
            case "Mean value":
                return data.mean()
            case "Minimum":
                return data.min()
            case "25 %":
                return data.quantile(0.25)    # TODO: variable for 0.25
            case "Median":
                return data.median()
            case "75 %":
                return data.quantile(0.75)
            case "Maximum":
                return data.max()
            case "Range":
                return data.max() - data.min()
            case "Interquartile range / H-spread":
                return data.quantile(0.75) - data.quantile(0.25)
            case "Modal value":
                return data.agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
            case "Modal value frequency":
                return data.agg(lambda x: x.value_counts().iloc[0] if not x.empty else 0)
            case "Standard deviation":
                return data.std()
            case "Variance":
                return data.var()
            case _:
                return None


def categorical_to_numerical(data_frame, attribute):
    pass


def numeric_to_categorical(data_frame, attribute):
    pass
