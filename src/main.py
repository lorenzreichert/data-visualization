import streamlit as st
import pandas as pd
import plotly.express as px
import io
import numpy as np
from nicegui import ui
import helpers
import math
import re

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
text_filter = st.text_input("Input text to include or exclude data rows")
filter_columns = st.multiselect("Select columns to which the filter applies", categorical_columns,
                                default=categorical_columns)
filtered_df = filtered_df[[col for col in df.columns if col in numeric_columns or col in filter_columns]]
drop_columns = [col for col in categorical_columns if col not in filter_columns]
is_included = st.toggle(
    "Include data rows that contain input text",
    value=True,
    help="""
        If toggled, the data rows containing the input text in one of the selected columns will be included in the data frame. 
        Otherwise, the data rows containing the input text in one of the selected columns will be excluded from the data frame.
    """)

if is_included:
    if text_filter:
        filtered_df = filtered_df.filter(like=text_filter, axis=0)
else:
    if text_filter:
        filtered_df = filtered_df.filter(regex=f"^(?!.*{re.escape(text_filter)}).*$", axis=0)

#  optional select (multiple) categorical attribute(s) for text input filter -> st.multiselect
#  optional toggle include or exclude -> st.toggle
#  ignore columns -> drop(list of columns, axis=1)

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
# Data information
# ---------------------------------------------------------
with st.expander("See data information"):
    st.subheader("Data information")
    df_measures = helpers.get_measures(filtered_df)
    st.dataframe(df_measures)

with st.expander("See attribute correlation"):
    st.info("Feature is not implemented yet")

# TODO: sort data ascending/descending
# TODO: more customization

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
            "Bar chart",  # x, y (numerical)
            "Histogram",
            "Line chart",  # x, y (numerical)
            "Pie chart",  # 1 attribute with share
            "Area chart",  # x, y (numerical), grouping?
            "Venn diagram",  # select X attributes and their shares
            "Stacked bar chart",  # x, y (numerical), grouping? -> share per bar
            "Scatterplot",  # x, y (numerical), categorical (colour), numeric (size)
            "Boxplot",  # x = categorical (optional), y = numerical
            "Top list sorted"  # Top X list of attribute Y (quantified), sorted (ascending/descending) by Y or Z(?)
        ]
    )

    # ---------------------------------------------------------
    # Create diagram
    # ---------------------------------------------------------
    match chart_type:
        case "Bar chart":
            # TODO: only allow those attributes on x axis that have less than 20 unique values
            # color (auch numeric attribute) distinguish between boolean or 3/4-option attributes
            # hover_data and labels with additional information
            # histogram option
            # text_auto enable/disable
            x_column = st.selectbox("X axis", df.columns)
            y_column = st.selectbox("Y axis", ["Count", "Unique", "Share"] + numeric_columns)
            color_attribute = st.selectbox("Color attribute", ["None"] + categorical_columns + numeric_columns)

            # ---------------------------------------------------------
            # numeric y column
            # ---------------------------------------------------------
            if y_column in numeric_columns:
                y_column_numeric_metric = st.selectbox(
                    "Metric",
                    ["Sum", "Mean value", "Minimum", "Median", "Maximum", "Range", "Interquartile range / H-spread",
                     "Modal value", "Modal value frequency", "Standard deviation", "Variance"]
                )

                grouped = filtered_df.groupby(x_column)[y_column]
                plot_df = helpers.get_metric(grouped, y_column_numeric_metric)
                plot_df = plot_df.reset_index(name="Value")
                diagram_title = f"{y_column_numeric_metric} of {y_column} by {x_column}"
            else:
                grouped = filtered_df.groupby(x_column)
                match y_column:
                    case "Count":
                        plot_df = grouped.size().reset_index(name="Value")
                        diagram_title = f"Count by {x_column}"
                    case "Unique":
                        unique_attribute = st.selectbox("Attribute", df.columns)
                        plot_df = grouped[unique_attribute].nunique().reset_index(name="Value")
                        diagram_title = f"Unique {unique_attribute} by {x_column}"
                    case "Share":
                        plot_df = (grouped.size().div(len(filtered_df)).mul(100)).reset_index(name="Value")
                        diagram_title = f"Share by {x_column}"
                    case _:
                        pass

            fig = px.bar(
                plot_df,
                x=x_column,
                y="Value",
                title=diagram_title,
                color=color_attribute if color_attribute != "None" else None
            )

        case "Histogram":
            st.info("This diagram type is not supported yet")

        case "Line chart":
            # color (und symbol) option to distinguish between boolean or 3/4-option attributes
            # sinnvollerweise ist wenn x=categorical ist, y=quantified(x) d.h. anzahl oder anteil (oder anzahl einzigartiger)
            # text option zum anzeigen für datenpunkte
            # markers option zum anzeigen von datenpunkten
            # hover_data and labels with additional information
            x_column = st.selectbox("X axis", df.columns)
            y_column = st.selectbox("Y axis", numeric_columns)

            fig = px.line(
                filtered_df,
                x=x_column,
                y=y_column,
                title=f"{y_column} vs {x_column}"
            )

        case "Pie chart":
            # names (grouping)
            # title
            # display share or total amount (boolean option)
            # hover_data and labels with additional information
            st.info("This diagram type is not supported yet")
            attribute = st.selectbox(df.columns)
            if attribute in numeric_columns:
                interval_size = st.number_input("Set the interval size", value=df[attribute].std(), min_value=0,
                                                max_value=df[attribute].max())
                start_interval_at = st.number_input("Start interval at",
                                                    min_value=math.floor(df[attribute].min() / 10) * 10)
                filtered_df = filtered_df[attribute]

            st.toggle(
                "Display percentages",
                value=True,
                help="""
                If toggled, the share of the respective attributes will be shown in percentages. 
                Otherwise, absolute numbers will be shown.
                """)

        case "Area chart":  # Area chart
            st.info("This diagram type is not supported yet")

        case "Venn diagram":  # Venn diagram
            st.info("This diagram type is not supported yet")

        case "Stacked bar chart":  # Stacked bar chart
            st.info("This diagram type is not supported yet")

        case "Scatterplot":  # Scatterplot
            x_column = st.selectbox("X axis", df.columns)
            y_column = st.selectbox("Y axis", numeric_columns)

            size_by_numerical = st.selectbox(
                "Select numerical attribute to display data points in different sizes (optional)",
                ["None"] + numeric_columns
            )

            color_by_categorical = st.selectbox(
                "Select categorical attribute to display data points in different colours (optional)",
                ["None"] + categorical_columns + numeric_columns
            )

            if color_by_categorical != "None" and color_by_categorical in numeric_columns:
                # TODO: Min value, max_value based on ...
                interval_size = st.number_input("Set the interval size", value=df[color_by_categorical].std(),
                                                min_value=0,
                                                max_value=df[color_by_categorical].max())
                start_interval_at = st.number_input("Start interval at",
                                                    min_value=math.floor(df[color_by_categorical].min() / 10) * 10)

            fig = px.scatter(
                filtered_df,
                x=x_column,
                y=y_column,
                size=size_by_numerical if size_by_numerical != "None" else None,
                color=color_by_categorical if color_by_categorical != "None" else None,
                title=f"{y_column} vs {x_column}",
            )

        case "Boxplot":  # Boxplot
            # x column (categorical) optional,
            # show all data points (boolean),
            # title (deduce from given numeric attribute),
            # notched True/False
            # color: distinguish between boolean or 3-option attributes
            # feature: grouped boxplots
            st.info("This diagram type is not yet supported")

        case "Top list sorted":  # List
            # todo integrate this into bar chart section, along with histogram -> normal bar chart, histogram or list
            st.info("This diagram type is not yet supported")
            st.slider("Select number of elements", 1, 25, 10)

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

with st.expander("Regression"):
    st.subheader("Regression")
    st.info("This feature is not implemented yet")
