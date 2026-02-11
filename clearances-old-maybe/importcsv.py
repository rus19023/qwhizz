# importcsv.py


import streamlit as st
import pandas as pd
import pymongo
from pymongo import MongoClient
import json
from datetime import datetime
import os
from io import StringIO

from report_module import *
from train_fuzzy_search import *


st.set_page_config(
    page_title='CSV Import App', 
    page_icon=':cherry_blossom:', 
    layout="wide", 
    initial_sidebar_state="auto", 
    menu_items=None
)


# Initialize connection to MongoDB
# Replace with your MongoDB connection string if needed
@st.cache_resource
def init_connection():
    try:
        return MongoClient("mongodb://localhost:27017/")
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

client = init_connection()

# App title and description
st.title("CSV to MongoDB Manager")
st.subheader("Import, Store, and Manage CSV Data")

# Sidebar for database and collection selection
st.sidebar.header("Database Settings")

if client:
    # Get list of databases
    dbs = client.list_database_names()
    # db_name = st.sidebar.selectbox("Select Database", [""] + dbs + ["Create New Database"])
    db_name = st.sidebar.selectbox("Select Database", ['temple_workers'] + ["Create New Database"])
    
    if db_name == "Create New Database":
        new_db_name = st.sidebar.text_input("Enter New Database Name")
        if new_db_name:
            db_name = new_db_name
    
    if db_name:
        db = client[db_name]
        collections = db.list_collection_names()
        collection_name = st.sidebar.selectbox("Select Collection", [""] + collections + ["Create New Collection"])
        
        if collection_name == "Create New Collection":
            new_collection_name = st.sidebar.text_input("Enter New Collection Name")
            if new_collection_name:
                collection_name = new_collection_name
        
        if collection_name:
            collection = db[collection_name]
            
            # Main content area
            tabs = st.tabs(["Import CSV", "View/Edit Data", "Schema Management"])
            
            # Import CSV tab
            with tabs[0]:
                st.header("Import CSV File")
                uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
                
                if uploaded_file is not None:
                    # Preview the data
                    df = pd.read_csv(uploaded_file)
                    st.write("Data Preview:")
                    st.dataframe(df.head())
                    
                    # Field mapping and customization
                    st.subheader("Field Mapping")
                    st.write("You can rename fields before importing to MongoDB")
                    
                    mapped_fields = {}
                    cols = df.columns.tolist()
                    
                    # Display field mapping widgets in columns to save space
                    col1, col2 = st.columns(2)
                    for i, col in enumerate(cols):
                        with col1 if i % 2 == 0 else col2:
                            mapped_fields[col] = st.text_input(f"Rename '{col}'", value=col, key=f"map_{col}")
                    
                    # Import options
                    st.subheader("Import Options")
                    replace_collection = st.checkbox("Replace existing collection data")
                    add_timestamp = st.checkbox("Add import timestamp", value=True)
                    
                    if st.button("Import to MongoDB"):
                        try:
                            # Rename columns according to mapping
                            df_to_import = df.copy()
                            df_to_import.columns = [mapped_fields.get(col, col) for col in df.columns]
                            
                            # Convert to dictionary records
                            records = df_to_import.to_dict("records")
                            
                            # Add timestamp if selected
                            if add_timestamp:
                                for record in records:
                                    record["import_timestamp"] = datetime.now()
                            
                            # Import to MongoDB
                            if replace_collection:
                                collection.delete_many({})
                            
                            if records:
                                result = collection.insert_many(records)
                                st.success(f"Successfully imported {len(result.inserted_ids)} records to MongoDB")
                        except Exception as e:
                            st.error(f"Error importing data: {e}")
            
            # View/Edit Data tab
            with tabs[1]:
                st.header("View and Edit Data")
                
                # Query options
                st.subheader("Query Options")
                query_field = st.selectbox("Filter by Field", ["No Filter"] + list(collection.find_one({}, {"_id": 0}).keys() if collection.find_one() else []))
                
                if query_field != "No Filter":
                    # Determine the type of the field for appropriate input
                    sample_doc = collection.find_one({})
                    if sample_doc and query_field in sample_doc:
                        field_type = type(sample_doc[query_field])
                        
                        if field_type == str:
                            query_value = st.text_input(f"Value for {query_field}")
                            query = {query_field: {"$regex": query_value, "$options": "i"}} if query_value else {}
                        elif field_type in [int, float]:
                            min_val, max_val = st.columns(2)
                            with min_val:
                                min_value = st.number_input(f"Min {query_field}", step=1 if field_type == int else 0.1)
                            with max_val:
                                max_value = st.number_input(f"Max {query_field}", 
                                                           value=float("inf") if field_type == float else int(1e9),
                                                           step=1 if field_type == int else 0.1)
                            query = {query_field: {"$gte": min_value, "$lte": max_value}}
                        else:
                            query_value = st.text_input(f"Value for {query_field}")
                            query = {query_field: query_value} if query_value else {}
                    else:
                        query_value = st.text_input(f"Value for {query_field}")
                        query = {query_field: query_value} if query_value else {}
                else:
                    query = {}
                
                # Load data
                limit = st.slider("Number of records to display", 5, 300, 20)
                
                if st.button("Load Data"):
                    try:
                        # Fetch data from MongoDB
                        cursor = collection.find(query).limit(limit)
                        data = list(cursor)
                        
                        # Convert ObjectId to string
                        for doc in data:
                            doc["_id"] = str(doc["_id"])
                            
                            # Convert datetime objects to strings for display
                            for key, value in doc.items():
                                if isinstance(value, datetime):
                                    doc[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                        
                        if not data:
                            st.warning("No data found matching your criteria")
                        else:
                            # Convert to DataFrame for display
                            df = pd.DataFrame(data)
                            
                            # Store the dataframe in session state for editing
                            st.session_state["edit_data"] = df
                            st.dataframe(df)
                            
                            # Export options
                            export_format = st.selectbox("Export Format", ["CSV", "JSON"])
                            
                            if st.button("Export Data"):
                                if export_format == "CSV":
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        label="Download CSV",
                                        data=csv,
                                        file_name=f"{collection_name}_export.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    # Convert to JSON with date handling
                                    json_str = df.to_json(orient="records", date_format="iso")
                                    st.download_button(
                                        label="Download JSON",
                                        data=json_str,
                                        file_name=f"{collection_name}_export.json",
                                        mime="application/json"
                                    )
                            
                            # Record editing
                            st.subheader("Edit Record")
                            record_id = st.selectbox("Select Record ID", df["_id"].tolist())
                            
                            if record_id:
                                selected_record = df[df["_id"] == record_id].iloc[0].to_dict()
                                
                                # Create form for editing
                                with st.form("edit_record_form"):
                                    edited_record = {}
                                    for key, value in selected_record.items():
                                        if key != "_id":  # Don't allow editing the ID
                                            edited_record[key] = st.text_input(f"Edit {key}", value=value)
                                    
                                    submit_button = st.form_submit_button("Update Record")
                                    
                                    if submit_button:
                                        try:
                                            # Update record in MongoDB
                                            update_result = collection.update_one(
                                                {"_id": json.loads(record_id) if record_id.startswith("{") else record_id},
                                                {"$set": edited_record}
                                            )
                                            
                                            if update_result.modified_count > 0:
                                                st.success("Record updated successfully")
                                            else:
                                                st.warning("No changes were made")
                                        except Exception as e:
                                            st.error(f"Error updating record: {e}")
                                
                                # Delete record option
                                if st.button("Delete Record"):
                                    try:
                                        delete_result = collection.delete_one(
                                            {"_id": json.loads(record_id) if record_id.startswith("{") else record_id}
                                        )
                                        
                                        if delete_result.deleted_count > 0:
                                            st.success("Record deleted successfully")
                                        else:
                                            st.warning("Failed to delete record")
                                    except Exception as e:
                                        st.error(f"Error deleting record: {e}")
                    
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
            
            # Schema Management tab
            with tabs[2]:
                st.header("Schema Management")
                
                try:
                    # Get current schema from a sample document
                    sample_doc = collection.find_one({}, {"_id": 0})
                    
                    if sample_doc:
                        st.subheader("Current Fields")
                        
                        # Display current fields and their types
                        schema_data = []
                        for field, value in sample_doc.items():
                            field_type = type(value).__name__
                            schema_data.append({"Field": field, "Type": field_type, "Sample": str(value)[:50]})
                        
                        schema_df = pd.DataFrame(schema_data)
                        st.dataframe(schema_df)
                        
                        # Schema operations
                        st.subheader("Schema Operations")
                        
                        # Rename field
                        with st.expander("Rename Field"):
                            fields = list(sample_doc.keys())
                            field_to_rename = st.selectbox("Select Field to Rename", fields)
                            new_field_name = st.text_input("New Field Name")
                            
                            if st.button("Rename Field") and new_field_name:
                                try:
                                    # MongoDB doesn't have a direct rename, so we need to copy and remove
                                    collection.update_many(
                                        {},
                                        {"$set": {new_field_name: f"${field_to_rename}"}},
                                        upsert=False
                                    )
                                    
                                    collection.update_many(
                                        {},
                                        {"$unset": {field_to_rename: ""}},
                                        upsert=False
                                    )
                                    
                                    st.success(f"Field '{field_to_rename}' renamed to '{new_field_name}'")
                                except Exception as e:
                                    st.error(f"Error renaming field: {e}")
                        
                        # Add new field
                        with st.expander("Add New Field"):
                            new_field = st.text_input("New Field Name")
                            default_value = st.text_input("Default Value")
                            
                            if st.button("Add Field") and new_field:
                                try:
                                    # Try to convert to appropriate type if possible
                                    try:
                                        # Try as int
                                        default_value_converted = int(default_value)
                                    except ValueError:
                                        try:
                                            # Try as float
                                            default_value_converted = float(default_value)
                                        except ValueError:
                                            # Keep as string
                                            default_value_converted = default_value
                                    
                                    collection.update_many(
                                        {},
                                        {"$set": {new_field: default_value_converted}},
                                        upsert=False
                                    )
                                    
                                    st.success(f"Field '{new_field}' added successfully")
                                except Exception as e:
                                    st.error(f"Error adding field: {e}")
                        
                        # Remove field
                        with st.expander("Remove Field"):
                            field_to_remove = st.selectbox("Select Field to Remove", fields, key="remove_field")
                            
                            if st.button("Remove Field"):
                                if st.checkbox("Confirm Removal", value=False):
                                    try:
                                        collection.update_many(
                                            {},
                                            {"$unset": {field_to_remove: ""}},
                                            upsert=False
                                        )
                                        
                                        st.success(f"Field '{field_to_remove}' removed successfully")
                                    except Exception as e:
                                        st.error(f"Error removing field: {e}")
                                else:
                                    st.warning("Please confirm the removal")
                        
                        # Index management
                        with st.expander("Manage Indexes"):
                            # Show current indexes
                            st.subheader("Current Indexes")
                            indexes = list(collection.list_indexes())
                            index_data = []
                            
                            for idx in indexes:
                                index_data.append({
                                    "Name": idx["name"],
                                    "Fields": str(idx["key"]),
                                    "Unique": idx.get("unique", False)
                                })
                            
                            st.dataframe(pd.DataFrame(index_data))
                            
                            # Create new index
                            st.subheader("Create New Index")
                            index_field = st.selectbox("Field to Index", fields)
                            index_unique = st.checkbox("Unique Index")
                            
                            if st.button("Create Index"):
                                try:
                                    collection.create_index([(index_field, pymongo.ASCENDING)], unique=index_unique)
                                    st.success(f"Index created on '{index_field}'")
                                except Exception as e:
                                    st.error(f"Error creating index: {e}")
                    else:
                        st.warning("No data found in collection. Import data first.")
                
                except Exception as e:
                    st.error(f"Error retrieving schema: {e}")

else:
    st.error("Failed to connect to MongoDB. Please check your connection.")

# Reports
render_report_builder(client, db_name, collection_name)


# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This application allows you to import CSV files into MongoDB, manage the data with full CRUD capabilities, 
and customize the schema by renaming or adding fields.
""")

# python -m streamlit run importcsv.py