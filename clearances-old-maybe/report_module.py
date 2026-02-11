# report_module.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import os
import base64
from io import BytesIO, StringIO
import pdfkit
from jinja2 import Template
import sys

# This module should be saved as report_module.py in the same directory as your main app
class MongoDBReporting:
    def __init__(self, client, db_name, collection_name):
        if not collection_name:
            raise ValueError("Collection name cannot be empty or None.")
        
        self.client = client
        self.db = client[db_name]
        self.collection = self.db[collection_name]

    def get_field_types(self):
        """Get all fields and their data types from the collection"""
        sample_doc = self.collection.find_one({}, {"_id": 0})
        if not sample_doc:
            return {}
        
        field_types = {}
        for field, value in sample_doc.items():
            field_type = type(value).__name__
            field_types[field] = field_type
        
        return field_types
    
    def get_numeric_fields(self):
        """Get list of numeric fields for analytics"""
        field_types = self.get_field_types()
        return [field for field, type_name in field_types.items() 
                if type_name in ('int', 'float', 'int64', 'float64')]
    
    def get_date_fields(self):
        """Get list of date fields for time-based analytics"""
        field_types = self.get_field_types()
        date_fields = []
        
        # Check each field
        for field, type_name in field_types.items():
            if type_name == 'datetime':
                date_fields.append(field)
            elif type_name == 'str':
                # Try to detect date strings
                sample_value = self.collection.find_one({field: {"$exists": True}}, {field: 1})
                if sample_value:
                    try:
                        if field.lower() in ['date', 'datetime', 'timestamp', 'created', 'modified', 'created_at', 'updated_at']:
                            # Try to parse as datetime
                            date_fields.append(field)
                    except:
                        pass
        
        return date_fields
    
    def get_categorical_fields(self, max_unique_values=20):
        """Get list of categorical fields (string fields with limited unique values)"""
        field_types = self.get_field_types()
        categorical_fields = []
        
        for field, type_name in field_types.items():
            if type_name == 'str':
                # Count unique values
                unique_count = len(self.collection.distinct(field))
                if 1 < unique_count <= max_unique_values:
                    categorical_fields.append(field)
        
        return categorical_fields
    
    def get_record_count(self, query=None):
        """Get count of records, optionally filtered by query"""
        if query is None:
            query = {}
        return self.collection.count_documents(query)
    
    def get_field_statistics(self, field):
        """Get basic statistics for a numeric field"""
        pipeline = [
            {"$match": {field: {"$type": ["int", "double", "long"]}}},
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avg": {"$avg": f"${field}"},
                "min": {"$min": f"${field}"},
                "max": {"$max": f"${field}"},
                "sum": {"$sum": f"${field}"}
            }}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None
    
    def generate_histogram(self, field, bins=10):
        """Generate histogram data for a numeric field"""
        data = list(self.collection.find({}, {field: 1, "_id": 0}))
        df = pd.DataFrame(data)
        
        if df.empty or field not in df.columns:
            return None
        
        return df[field].dropna()
    
    def generate_categorical_chart_data(self, field, limit=10):
        """Generate data for categorical fields (bar charts, pie charts)"""
        pipeline = [
            {"$match": {field: {"$exists": True, "$ne": ""}}},
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        # Convert to dataframe
        chart_data = pd.DataFrame(result)
        if not chart_data.empty:
            chart_data.columns = ['category', 'count']
        
        return chart_data
    
    def generate_time_series_data(self, date_field, value_field=None, interval="day", query=None):
        """Generate time series data for a date field"""
        if query is None:
            query = {}
        
        # Define group ID based on interval
        if interval == "day":
            group_id = {"$dateToString": {"format": "%Y-%m-%d", "date": f"${date_field}"}}
        elif interval == "week":
            group_id = {"$dateToString": {"format": "%Y-%U", "date": f"${date_field}"}}
        elif interval == "month":
            group_id = {"$dateToString": {"format": "%Y-%m", "date": f"${date_field}"}}
        else:
            group_id = {"$dateToString": {"format": "%Y-%m-%d", "date": f"${date_field}"}}
        
        # Build aggregation pipeline
        pipeline = [
            {"$match": {**query, date_field: {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": group_id,
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        # If a value field is specified, add it to the aggregation
        if value_field:
            pipeline[1]["$group"]["value"] = {"$sum": f"${value_field}"}
        
        result = list(self.collection.aggregate(pipeline))
        
        # Convert to dataframe
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        df.columns = ['date'] + (['count'] if 'count' in df.columns else []) + (['value'] if value_field else [])
        
        try:
            # Convert string dates back to datetime
            if interval == "day":
                df['date'] = pd.to_datetime(df['date'])
            elif interval == "week":
                # Parse year-week format
                df['date'] = pd.to_datetime(df['date'] + '-1', format='%Y-%U-%w')
            elif interval == "month":
                # Parse year-month format
                df['date'] = pd.to_datetime(df['date'] + '-01')
        except Exception as e:
            print(f"Error converting dates: {e}")
        
        return df
    
    def generate_correlation_data(self, fields):
        """Generate correlation matrix for selected numeric fields"""
        if not fields or len(fields) < 2:
            return None

        projection = {field: 1 for field in fields}
        projection["_id"] = 0

        data = list(self.collection.find({}, projection))
        df = pd.DataFrame(data)

        if df.empty:
            return None

        # Attempt to coerce values to numeric where possible
        numeric_df = df.apply(pd.to_numeric, errors="coerce")

        # Drop columns that are entirely NaN after coercion
        numeric_df = numeric_df.dropna(axis=1, how="all")

        # Need at least 2 numeric columns for correlation
        if numeric_df.shape[1] < 2:
            return None

        return numeric_df.corr()

    
    def run_pipeline_query(self, pipeline):
        """Run a custom aggregation pipeline query"""
        try:
            if isinstance(pipeline, str):
                pipeline = json.loads(pipeline)
            result = list(self.collection.aggregate(pipeline))
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def export_to_excel(self, query=None, filename="report.xlsx"):
        """Export report data to Excel file"""
        if query is None:
            query = {}
        
        data = list(self.collection.find(query))
        df = pd.DataFrame(data)
        
        # Convert ObjectId to string
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Add a stats sheet
            stats = []
            for col in df.columns:
                if df[col].dtype.kind in 'ifc':  # integer, float, complex
                    stats.append({
                        'Field': col,
                        'Count': df[col].count(),
                        'Mean': df[col].mean() if df[col].dtype.kind in 'fc' else None,
                        'Min': df[col].min(),
                        'Max': df[col].max(),
                        'Sum': df[col].sum() if df[col].dtype.kind in 'ifc' else None
                    })
            
            if stats:
                stats_df = pd.DataFrame(stats)
                stats_df.to_excel(writer, index=False, sheet_name='Statistics')
        
        buffer.seek(0)
        return buffer
    
    def export_to_csv(self, query=None):
        """Export report data to CSV"""
        if query is None:
            query = {}
        
        data = list(self.collection.find(query))
        df = pd.DataFrame(data)
        
        # Convert ObjectId to string
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        
        return df.to_csv(index=False)
    
    def generate_pdf_report(self, report_title, components):
        """Generate a PDF report with the specified components"""
        try:
            # HTML template for the report
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ title }}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333366; }
                    h2 { color: #666699; margin-top: 20px; }
                    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    .image-container { text-align: center; margin: 20px 0; }
                    .image-container img { max-width: 100%; }
                    .footer { margin-top: 30px; font-size: 12px; color: #666; text-align: center; }
                </style>
            </head>
            <body>
                <h1>{{ title }}</h1>
                <p>Report generated on {{ date }}</p>
                
                {% for component in components %}
                    <div class="component">
                        <h2>{{ component.title }}</h2>
                        
                        {% if component.type == 'text' %}
                            <p>{{ component.content }}</p>
                        
                        {% elif component.type == 'table' %}
                            {{ component.content }}
                        
                        {% elif component.type == 'image' %}
                            <div class="image-container">
                                <img src="data:image/png;base64,{{ component.content }}" alt="{{ component.title }}">
                            </div>
                        
                        {% elif component.type == 'stats' %}
                            <table>
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th>Value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for key, value in component.content.items() %}
                                    <tr>
                                        <td>{{ key }}</td>
                                        <td>{{ value }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        {% endif %}
                    </div>
                {% endfor %}
                
                <div class="footer">
                    Generated by MongoDB Reporting Module
                </div>
            </body>
            </html>
            """
            
            # Prepare report data
            template = Template(html_template)
            html_content = template.render(
                title=report_title,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                components=components
            )
            
            # Generate PDF
            pdf = pdfkit.from_string(html_content, False)
            return pdf
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None


def render_report_builder(client, db_name, collection_name):
    """Render the report builder interface in Streamlit"""
    if collection_name:
    
        # Initialize the reporting module
        report_module = MongoDBReporting(client, db_name, collection_name)
        
        st.title("Report Builder")
        st.subheader(f"Building reports for {db_name}.{collection_name}")
        
        # Sidebar for report configuration
        st.sidebar.header("Report Settings")
        report_title = st.sidebar.text_input("Report Title", f"Clearances Needed")
        
        # Get field information
        field_types = report_module.get_field_types()
        numeric_fields = report_module.get_numeric_fields()
        date_fields = report_module.get_date_fields()
        categorical_fields = report_module.get_categorical_fields()
        
        # # Display field information
        # if st.sidebar.checkbox("Show Field Types", value=False):
        #     st.sidebar.subheader("Field Types")
        #     for field, field_type in field_types.items():
        #         st.sidebar.text(f"{field}: {field_type}")
        
        # Report components
        st.subheader("Report Components")
        #tabs = st.tabs(["Basic Statistics", "Charts", "Time Series", "Cross Analysis", "Custom Query", "Export"])
        tabs = st.tabs(["All Clearances", "Expired", "Incomplete", "No Paperwork Submitted", "New Workers", "", "", "", "", "", "Custom Query", "", ""])
        
        # Clearances Report Tab
    with tabs[0]:
        st.header("Clearances Report")

        REPORT_FIELDS = [
            "Name",
            "Personal Phone",
            "Email",
            "Shift Name",
            "Frequencies",
            "Protecting Children and Youth",
            "Skills"
        ]

        # --- Sort state ---
        if "people_sort" not in st.session_state:
            st.session_state.people_sort = []

        # --- FILTER UI ---
        st.subheader("Filter")
        filter_fields = st.multiselect("Fields to search", REPORT_FIELDS, default=REPORT_FIELDS)
        search_term = st.text_input("Search text")

        # --- BUILD MONGO QUERY ---
        mongo_query = {}
        if search_term and filter_fields:
            mongo_query["$or"] = [
                {field: {"$regex": search_term, "$options": "i"}}
                for field in filter_fields
            ]

        # --- CLICKABLE SORT HEADERS ---
        st.subheader("Sort (click column names)")
        header_cols = st.columns(len(REPORT_FIELDS))

        for i, field in enumerate(REPORT_FIELDS):
            indicator = ""
            for idx, (col, asc) in enumerate(st.session_state.people_sort):
                if col == field:
                    indicator = f" {'▲' if asc else '▼'} ({idx+1})"

            if header_cols[i].button(field + indicator, key=f"sort_{field}"):
                existing = next((i for i, v in enumerate(st.session_state.people_sort) if v[0] == field), None)
                if existing is not None:
                    col, asc = st.session_state.people_sort[existing]
                    st.session_state.people_sort[existing] = (col, not asc)
                else:
                    if len(st.session_state.people_sort) == 3:
                        st.session_state.people_sort.pop(0)
                    st.session_state.people_sort.append((field, True))
                st.rerun()

        # --- MONGO SORT ---
        mongo_sort = None
        if st.session_state.people_sort:
            mongo_sort = [(col, 1 if asc else -1) for col, asc in st.session_state.people_sort]

        # --- FETCH DATA ---
        projection = {field: 1 for field in REPORT_FIELDS}
        projection["_id"] = 0

        cursor = report_module.collection.find(mongo_query, projection)
        if mongo_sort:
            cursor = cursor.sort(mongo_sort)

        df = pd.DataFrame(list(cursor))
        if df.empty:
            st.info("No matching records.")
            st.stop()

        # --- NORMALIZATION ---
        # df["Personal Phone"] = df["Personal Phone"].apply(normalize_phone)
        # df["Email"] = df["Email"].apply(normalize_email)

        # --- HTML RENDERING ---
        display_df = df.copy()
        # display_df["Personal Phone"] = display_df["Personal Phone"].apply(
        #     lambda v: f"{v}{copy_button(v)}"
        # )
        # display_df["Email"] = display_df["Email"].apply(
        #     lambda v: f"{v}{copy_button(v)}"
        # )
        # display_df["Skills"] = display_df["Skills"].apply(render_skill_badges)

        st.markdown(
            display_df[REPORT_FIELDS].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

        # --- CSV EXPORT (Clearances REPORT ONLY) ---
        st.download_button(
            "Download Clearances Report (CSV)",
            data=df[REPORT_FIELDS].to_csv(index=False),
            file_name="Clearances_report.csv",
            mime="text/csv"
        )

        # --- ADD TO MAIN EXPORT ---
        if st.button("Add Clearances Report to Export"):
            if "report_components" not in st.session_state:
                st.session_state.report_components = []

            st.session_state.report_components.append({
                "title": "Clearances Report",
                "type": "table",
                "content": display_df[REPORT_FIELDS].to_html(escape=False, index=False)
            })

            st.success("Clearances Report added to export.")

            
            
        
        # Basic Statistics Tab
        with tabs[6]:
            st.header("Basic Statistics")
            
            # Record count
            total_records = report_module.get_record_count()
            st.metric("Total Records", total_records)
            
            if numeric_fields:
                # Numeric field statistics
                stats_field = st.selectbox("Select field for statistics", numeric_fields)
                
                if stats_field:
                    stats = report_module.get_field_statistics(stats_field)
                    if stats:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Average", round(stats['avg'], 2))
                        with col2:
                            st.metric("Minimum", stats['min'])
                        with col3:
                            st.metric("Maximum", stats['max'])
                        with col4:
                            st.metric("Sum", round(stats['sum'], 2))
                        
                        # Option to add to report
                        if st.button("Add Statistics to Report", key="add_stats"):
                            if 'report_components' not in st.session_state:
                                st.session_state.report_components = []
                            
                            st.session_state.report_components.append({
                                'title': f"Statistics for {stats_field}",
                                'type': 'stats',
                                'content': {
                                    'Average': round(stats['avg'], 2),
                                    'Minimum': stats['min'],
                                    'Maximum': stats['max'],
                                    'Sum': round(stats['sum'], 2),
                                    'Count': stats['count']
                                }
                            })
                            
                            st.success(f"Added statistics for {stats_field} to report")
                    else:
                        st.warning(f"No numeric data found for {stats_field}")
        
        # Charts Tab
        with tabs[7]:
            st.header("Data Visualization")
            
            chart_type = st.selectbox("Chart Type", 
                                    ["Bar Chart", "Pie Chart", "Histogram"])
            
            if chart_type in ["Bar Chart", "Pie Chart"] and categorical_fields:
                # Fields suitable for bar/pie charts
                field = st.selectbox("Select categorical field", categorical_fields)
                limit = st.slider("Number of categories to show", 3, 20, 10)
                
                if field:
                    chart_data = report_module.generate_categorical_chart_data(field, limit)
                    
                    if not chart_data.empty:
                        if chart_type == "Bar Chart":
                            fig = px.bar(chart_data, x='category', y='count', 
                                        title=f"Distribution of {field}")
                            st.plotly_chart(fig, width=True)
                        else:
                            fig = px.pie(chart_data, names='category', values='count', 
                                        title=f"Distribution of {field}")
                            st.plotly_chart(fig, width=True)
                        
                        # Add to report option
                        if st.button("Add Chart to Report", key="add_cat_chart"):
                            if 'report_components' not in st.session_state:
                                st.session_state.report_components = []
                            
                            # Convert Plotly figure to image
                            img_bytes = fig.to_image(format="png")
                            encoded = base64.b64encode(img_bytes).decode("ascii")
                            
                            st.session_state.report_components.append({
                                'title': f"Distribution of {field}",
                                'type': 'image',
                                'content': encoded
                            })
                            
                            st.success(f"Added {chart_type} to report")
                    else:
                        st.warning(f"No categorical data found for {field}")
            
            elif chart_type == "Histogram" and numeric_fields:
                # Fields suitable for histograms
                field = st.selectbox("Select numeric field", numeric_fields)
                bins = st.slider("Number of bins", 5, 50, 10)
                
                if field:
                    hist_data = report_module.generate_histogram(field, bins)
                    
                    if hist_data is not None and not hist_data.empty:
                        fig = px.histogram(hist_data, x=field, nbins=bins,
                                        title=f"Histogram of {field}")
                        st.plotly_chart(fig, width=True)
                        
                        # Add to report option
                        if st.button("Add Histogram to Report"):
                            if 'report_components' not in st.session_state:
                                st.session_state.report_components = []
                            
                            # Convert Plotly figure to image
                            img_bytes = fig.to_image(format="png")
                            encoded = base64.b64encode(img_bytes).decode("ascii")
                            
                            st.session_state.report_components.append({
                                'title': f"Histogram of {field}",
                                'type': 'image',
                                'content': encoded
                            })
                            
                            st.success("Added histogram to report")
                    else:
                        st.warning(f"No numeric data found for {field}")
            else:
                st.info("No suitable fields found for this chart type")
        
        # Time Series Tab
        with tabs[8]:
            st.header("Time Series Analysis")
            
            if date_fields:
                date_field = st.selectbox("Select date field", date_fields)
                value_field = st.selectbox("Select value field (optional)", 
                                        ["Count Only"] + numeric_fields)
                interval = st.selectbox("Interval", ["Day", "Week", "Month"])
                
                if date_field:
                    # Get time series data
                    timeseries_data = report_module.generate_time_series_data(
                        date_field, 
                        None if value_field == "Count Only" else value_field,
                        interval.lower()
                    )
                    
                    if not timeseries_data.empty:
                        fig = px.line(timeseries_data, x='date', 
                                    y='value' if value_field != "Count Only" else 'count',
                                    title=f"{value_field} by {interval}")
                        st.plotly_chart(fig, width=True)
                        
                        # Add to report option
                        if st.button("Add Time Series to Report"):
                            if 'report_components' not in st.session_state:
                                st.session_state.report_components = []
                            
                            # Convert Plotly figure to image
                            img_bytes = fig.to_image(format="png")
                            encoded = base64.b64encode(img_bytes).decode("ascii")
                            
                            st.session_state.report_components.append({
                                'title': f"{value_field} by {interval}",
                                'type': 'image',
                                'content': encoded
                            })
                            
                            st.success("Added time series to report")
                    else:
                        st.warning(f"No time series data found for {date_field}")
            else:
                st.info("No date fields found in the collection")
        
        # Cross Analysis Tab
        with tabs[9]:
            st.header("Cross Analysis")
            
            if len(numeric_fields) >= 2:
                analysis_type = st.selectbox("Analysis Type", ["Correlation Matrix", "Scatter Plot"])
                
                if analysis_type == "Correlation Matrix":
                    selected_fields = st.multiselect("Select fields for correlation", 
                                                numeric_fields, 
                                                default=numeric_fields[:min(5, len(numeric_fields))])
                    
                    if len(selected_fields) >= 2:
                        corr_data = report_module.generate_correlation_data(selected_fields)
                        
                        if corr_data is not None:
                            fig = px.imshow(corr_data, text_auto=True, 
                                        aspect="auto", color_continuous_scale='RdBu_r',
                                        title="Correlation Matrix")
                            st.plotly_chart(fig, width=True)
                            
                            # Add to report option
                            if st.button("Add Correlation Matrix to Report"):
                                if 'report_components' not in st.session_state:
                                    st.session_state.report_components = []
                                
                                # Convert Plotly figure to image
                                img_bytes = fig.to_image(format="png")
                                encoded = base64.b64encode(img_bytes).decode("ascii")
                                
                                st.session_state.report_components.append({
                                    'title': "Correlation Matrix",
                                    'type': 'image',
                                    'content': encoded
                                })
                                
                                st.success("Added correlation matrix to report")
                        else:
                            st.warning("Could not generate correlation matrix")
                
                elif analysis_type == "Scatter Plot":
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        x_field = st.selectbox("X-axis field", numeric_fields)
                    
                    with col2:
                        y_field = st.selectbox("Y-axis field", 
                                            [f for f in numeric_fields if f != x_field])
                    
                    if x_field and y_field:
                        # Fetch data
                        data = list(report_module.collection.find(
                            {x_field: {"$exists": True}, y_field: {"$exists": True}},
                            {x_field: 1, y_field: 1, "_id": 0}
                        ))
                        
                        df = pd.DataFrame(data)
                        
                        if not df.empty:
                            fig = px.scatter(df, x=x_field, y=y_field, 
                                        title=f"{y_field} vs {x_field}")
                            
                            # Add trend line
                            fig.update_layout(xaxis_title=x_field, yaxis_title=y_field)
                            st.plotly_chart(fig, width=True)
                            
                            # Add to report option
                            if st.button("Add Scatter Plot to Report"):
                                if 'report_components' not in st.session_state:
                                    st.session_state.report_components = []
                                
                                # Convert Plotly figure to image
                                img_bytes = fig.to_image(format="png")
                                encoded = base64.b64encode(img_bytes).decode("ascii")
                                
                                st.session_state.report_components.append({
                                    'title': f"{y_field} vs {x_field}",
                                    'type': 'image',
                                    'content': encoded
                                })
                                
                                st.success("Added scatter plot to report")
                        else:
                            st.warning(f"No data found for {x_field} and {y_field}")
            else:
                st.info("Need at least 2 numeric fields for cross analysis")
        
        # Custom Query Tab
        with tabs[10]:
            st.header("Custom MongoDB Aggregation")
            
            st.info("Write a MongoDB aggregation pipeline in JSON format")
            
            # Example aggregation pipeline
            example_pipeline = """[
        {"$group": {"_id": "$field_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]"""
            
            pipeline_query = st.text_area("Aggregation Pipeline", 
                                        example_pipeline, 
                                        height=200)
            
            if st.button("Run Query"):
                try:
                    results = report_module.run_pipeline_query(pipeline_query)
                    
                    if isinstance(results, list):
                        df = pd.DataFrame(results)
                        st.dataframe(df)
                        
                        # Add to report option
                        if not df.empty and st.button("Add Query Results to Report"):
                            if 'report_components' not in st.session_state:
                                st.session_state.report_components = []
                            
                            # Convert dataframe to HTML table
                            html_table = df.to_html(index=False)
                            
                            st.session_state.report_components.append({
                                'title': "Custom Query Results",
                                'type': 'table',
                                'content': html_table
                            })
                            
                            st.success("Added query results to report")
                    elif isinstance(results, dict) and 'error' in results:
                        st.error(f"Query error: {results['error']}")
                    else:
                        st.warning("No results returned")
                except Exception as e:
                    st.error(f"Error running query: {e}")
        
        # Export Tab
        with tabs[11]:
            st.header("Export Reports")
            
            # Show current report components
            if 'report_components' in st.session_state and st.session_state.report_components:
                st.subheader("Current Report Components")
                
                for i, component in enumerate(st.session_state.report_components):
                    st.text(f"{i+1}. {component['title']} ({component['type']})")
                
                # Option to remove components
                remove_idx = st.number_input("Remove component (enter index)", 
                                        min_value=0, 
                                        max_value=len(st.session_state.report_components),
                                        value=0)
                
                if remove_idx > 0 and st.button("Remove Selected Component"):
                    st.session_state.report_components.pop(remove_idx - 1)
                    st.success(f"Removed component {remove_idx}")
                    st.rerun()
                
                # Export options
                export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV"])
                
                if st.button("Generate Report"):
                    try:
                        if export_format == "PDF":
                            pdf_bytes = report_module.generate_pdf_report(
                                report_title, 
                                st.session_state.report_components
                            )
                            
                            if pdf_bytes:
                                st.download_button(
                                    label="Download PDF Report",
                                    data=pdf_bytes,
                                    file_name=f"{report_title.replace(' ', '_')}.pdf",
                                    mime="application/pdf"
                                )
                        
                        elif export_format == "Excel":
                            excel_buffer = report_module.export_to_excel()
                            
                            st.download_button(
                                label="Download Excel Report",
                                data=excel_buffer,
                                file_name=f"{report_title.replace(' ', '_')}.xlsx",
                                mime="application/vnd.ms-excel"
                            )
                        
                        elif export_format == "CSV":
                            csv_data = report_module.export_to_csv()
                            
                            st.download_button(
                                label="Download CSV Report",
                                data=csv_data,
                                file_name=f"{report_title.replace(' ', '_')}.csv",
                                mime="text/csv"
                            )
                    
                    except Exception as e:
                        st.error(f"Error generating report: {e}")
            else:
                if 'report_components' not in st.session_state:
                    st.session_state.report_components = []
                
                st.info("No report components added yet. Add components from the other tabs.")
        
        # Add some text components directly
        st.sidebar.subheader("Add Text Component")
        text_title = st.sidebar.text_input("Text Component Title")
        text_content = st.sidebar.text_area("Text Content")
        
        if st.sidebar.button("Add Text to Report"):
            if 'report_components' not in st.session_state:
                st.session_state.report_components = []
            
            st.session_state.report_components.append({
                'title': text_title or "Text Section",
                'type': 'text',
                'content': text_content
            })
            
            st.sidebar.success("Added text component to report")
        
        # Clear report option
        if 'report_components' in st.session_state and st.session_state.report_components:
            if st.sidebar.button("Clear All Report Components"):
                st.session_state.report_components = []
                st.sidebar.success("Cleared all report components")
                st.rerun()