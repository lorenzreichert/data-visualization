import streamlit as st
import pandas as pd
import plotly.express as px
import io
import numpy as np
from nicegui import ui
import helpers

# ---------------------------------------------------------
# UI config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Data Visualization Project",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------------
# Upload file
# ---------------------------------------------------------
file = st.file_uploader(
    "Select csv or xlsx file",
    type=["csv", "xlsx"]
)

# ---------------------------------------------------------
# Data frame
# ---------------------------------------------------------
if file is None:
    st.info("Please upload csv or xlsx file")
    st.stop()

try:
    df, selected_sheet = helpers.load_data(file)

except Exception as e:
    st.error(f"Error occurred: {e}")
    st.stop()

if df.empty:
    st.warning("Uploaded file doesn't contain data")
    st.stop()

# ---------------------------------------------------------
# Basic file information
# ---------------------------------------------------------
st.subheader(f"File: {file.name}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Lines", f"{len(df):,}")

with col2:
    st.metric("Columns", f"{len(df.columns):,}")

with col3:
    st.metric("File size", f"{file.size / 1024:.1f} KB")

# ---------------------------------------------------------
# Detect column types
# ---------------------------------------------------------
numeric_columns = df.select_dtypes(include="number").columns.tolist()
categorical_columns = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
date_columns = df.select_dtypes(include=["datetime"]).columns.tolist()

# ---------------------------------------------------------
# Filter
# ---------------------------------------------------------
st.sidebar.header("Filter")
filtered_df = df.copy()

# ---------------------------------------------------------
# Category filter
# ---------------------------------------------------------
for column in categorical_columns:
    unique_values = df[column].dropna().unique()

    if len(unique_values) <= 50:
        selected_values = st.sidebar.multiselect(
            column,
            options=sorted(unique_values, key=str),
            default=list(unique_values)
        )
        filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

# ---------------------------------------------------------
# Numeric filter
# ---------------------------------------------------------
for column in numeric_columns:
    min_value = float(df[column].min())
    max_value = float(df[column].max())

    if min_value != max_value:
        selected_range = st.sidebar.slider(
            column,
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value)
        )

        filtered_df = filtered_df[filtered_df[column].between(
            selected_range[0], selected_range[1]
        )]

# ---------------------------------------------------------
# Result
# ---------------------------------------------------------
st.subheader("Filtered data")

st.write(f"{len(filtered_df):,} of {len(df):,} lines")
st.dataframe(filtered_df, use_container_width=True, height=400)

# ---------------------------------------------------------
# CSV download
# ---------------------------------------------------------
st.subheader("Export")
csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv_data,
    file_name="filtered_data.csv",
    mime="text/csv",
)

# ---------------------------------------------------------
# Data information
# ---------------------------------------------------------
st.subheader("Data information")
df_measures = helpers.get_measures(filtered_df)
st.dataframe(df_measures)

# TODO: sort data ascending/descending
# TODO: more customization
# ---------------------------------------------------------
# Visualization
# ---------------------------------------------------------
st.subheader("Visualization")
if len(numeric_columns) == 0:
    st.info("No numeric columns found.")
    st.info("At least one numeric columns needed for diagrams")

else:

    # datetime -> categoric: year, month, calendar week
    # numeric -> categoric: interval of X years, starting with -> Year / X (include factor starting with)
    # interval = Year / X * 10 + startingWithFactor to Year / X * 10 + startingWithFactor + X - 1
    chart_type = st.selectbox(
        "Diagram type",
        [
            "Bar chart",  # x, y
            "Line chart",  # x, y
            "Pie chart",  # 1 attribute (categorical) with share
            "Area chart",  # x, y, grouping?
            "Venn diagram",  # select X attributes and their shares
            "Stacked bar chart",  # x, y, grouping? -> share per bar
            "Scatterplot",  # x, y, categorical (colour), numeric (size)
            "Boxplot",
            "Heatmap",
            "Top list sorted"  # Top X list of attribute Y (quantified), sorted (ascending/descending) by Y or Z(?)
        ]
    )

    x_column = st.selectbox(
        "X axis",
        df.columns
    )

    y_column = st.selectbox(
        "Y axis",
        numeric_columns
    )

    # ---------------------------------------------------------
    # Create diagram
    # ---------------------------------------------------------
    if chart_type == "Bar chart":
        fig = px.bar(
            filtered_df,
            x=x_column,
            y=y_column,
            title=f"{y_column} vs {x_column}",
        )

    elif chart_type == "Line chart":
        fig = px.line(
            filtered_df,
            x=x_column,
            y=y_column,
            title=f"{y_column} vs {x_column}",
        )

    elif chart_type == "Scatterplot":
        size_by_numerical = st.selectbox(
            "Select numerical attribute to display data points in different sizes (optional)",
            ["None"] + numeric_columns
        )

        color_by_categorical = st.selectbox(
            "Select categorical attribute to display data points in different colours (optional)",
            ["None"] + categorical_columns
        )

        fig = px.scatter(
            filtered_df,
            x=x_column,
            y=y_column,
            size=size_by_numerical if size_by_numerical != "None" else None,
            color=color_by_categorical if color_by_categorical != "None" else None,
            title=f"{y_column} vs {x_column}",
        )

    else:
        st.info("This diagram type is not yet supported")
        st.stop()

    # ---------------------------------------------------------
    # Show diagram
    # ---------------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # Download diagram
    # ---------------------------------------------------------
    try:
        png_data = fig.to_image(format="png", width=1600, height=900)

        st.download_button(
            label="Download diagram as PNG",
            data=png_data,
            file_name="diagram.png",
            mime="image/png",
        )
    except Exception as e:
        st.warning(
            "PNG download not available. "
            "Is 'kaleido' installed?"
        )
