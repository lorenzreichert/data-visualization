import pandas as pd
import streamlit as st


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
    measures = ["Count", "Unique", "Mean value", "Minimum", "25 %", "Median", "75 %", "Maximum", "Range",
                "Interquartile range / H-spread", "Modal value", "Modal value frequency", "Standard deviation",
                "Variance"]
    data_frame.describe(include="all")
