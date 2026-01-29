import streamlit as st
import pandas as pd
import pymongo
from pymongo import MongoClient
from datetime import datetime
from report_module import *
from train_fuzzy_search import *

# ============= Configuration =============
st.set_page_config(
    page_title='PA Child Protection Clearances',
    page_icon='👼',
    layout="wide",
    initial_sidebar_state="auto"
)

# ============= Helper Functions =============
@st.cache_resource
def init_connection():
    try:
        return MongoClient("mongodb://localhost:27017/")
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

def convert_doc_for_display(doc):
    """Convert MongoDB document for display"""
    doc["_id"] = str(doc["_id"])
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.strftime("%Y-%m-%d %H:%M:%S")
    return doc

def get_or_create_collection(client, sidebar):
    """Handle database and collection selection/creation"""
    sidebar.header("Database Settings")
    
    #db_name = sidebar.selectbox("Select Database", ['temple_workers', "Create New Database"], key="db_select")
    #if db_name == "Create New Database":
    db_name = "temple_workers" #sidebar.text_input("Enter New Database Name", key="new_db_name")
    
    if not db_name:
        return None, None, None
    
    db = client[db_name]
    collections = db.list_collection_names()
    # collection_name = sidebar.selectbox("Select Collection", [""] + collections + ["Create New Collection"], key="collection_select")
    collection_name = 'Clearances'
    
    if collection_name == "Create New Collection":
        collection_name = sidebar.text_input("Enter New Collection Name", key="new_collection_name")
    
    return (db[collection_name], collection_name, db_name) if collection_name else (None, None, None)

# ============= Tab Content Functions =============
def render_import_tab(collection):
    """Import CSV tab"""
    st.header("Import CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if not uploaded_file:
        return
    
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview:")
    st.dataframe(df.head())
    
    # Field mapping
    st.subheader("Field Mapping")
    mapped_fields = {}
    col1, col2 = st.columns(2)
    for i, col in enumerate(df.columns):
        with col1 if i % 2 == 0 else col2:
            mapped_fields[col] = st.text_input(f"Rename '{col}'", value=col, key=f"map_{col}")
    
    # New field configuration
    st.subheader("Add New Fields")
    num_new_fields = st.number_input("Number of new fields to add", min_value=0, max_value=10, value=0)
    new_fields = {}
    
    if num_new_fields > 0:
        for i in range(num_new_fields):
            col1, col2, col3 = st.columns(3)
            with col1:
                field_name = st.text_input(f"Field {i+1} Name", key=f"new_field_name_{i}")
            with col2:
                field_type = st.selectbox(
                    f"Field {i+1} Type",
                    ["text", "number", "date", "boolean"],
                    key=f"new_field_type_{i}"
                )
            with col3:
                field_value = st.text_input(f"Field {i+1} Default Value", key=f"new_field_value_{i}")
            
            if field_name:
                new_fields[field_name] = {"type": field_type, "value": field_value}
    
    # Import options
    st.subheader("Import Options")
    replace_collection = st.checkbox("Replace existing collection data")
    add_timestamp = st.checkbox("Add import timestamp", value=True)
    process_multiline = st.checkbox("Split fields on line breaks into arrays", value=False)
    
    if st.button("Import to MongoDB"):
        try:
            df_to_import = df.rename(columns=mapped_fields)
            records = df_to_import.to_dict("records")
            
            # Process each record
            for record in records:
                # Add timestamp if requested
                if add_timestamp:
                    record["import_timestamp"] = datetime.now()
                
                # Add new fields
                for field_name, field_config in new_fields.items():
                    field_value = field_config["value"]
                    field_type = field_config["type"]
                    
                    # Convert value based on type
                    if field_type == "number" and field_value:
                        record[field_name] = float(field_value)
                    elif field_type == "boolean":
                        record[field_name] = field_value.lower() in ["true", "1", "yes"]
                    elif field_type == "date" and field_value:
                        record[field_name] = datetime.fromisoformat(field_value)
                    else:
                        record[field_name] = field_value
                
                # Process multiline fields if requested
                if process_multiline:
                    for key, value in record.items():
                        if isinstance(value, str) and '\n' in value:
                            # Split on line breaks and remove empty lines
                            record[key] = [line.strip() for line in value.split('\n') if line.strip()]
            
            if replace_collection:
                collection.delete_many({})
            
            if records:
                result = collection.insert_many(records)
                st.success(f"Successfully imported {len(result.inserted_ids)} records")
                
                # Show summary of new fields added
                if new_fields:
                    st.info(f"Added {len(new_fields)} new field(s): {', '.join(new_fields.keys())}")
        except Exception as e:
            st.error(f"Error importing data: {e}")
            

def build_query(collection, query_field):
    """Build MongoDB query from user input"""
    if query_field == "No Filter":
        return {}
    
    sample_doc = collection.find_one({})
    if not sample_doc or query_field not in sample_doc:
        query_value = st.text_input(f"Value for {query_field}")
        return {query_field: query_value} if query_value else {}
    
    field_type = type(sample_doc[query_field])
    
    if field_type == str:
        query_value = st.text_input(f"Value for {query_field}")
        return {query_field: {"$regex": query_value, "$options": "i"}} if query_value else {}
    
    if field_type in [int, float]:
        col1, col2 = st.columns(2)
        with col1:
            min_value = st.number_input(f"Min {query_field}", step=1 if field_type == int else 0.1)
        with col2:
            max_value = st.number_input(f"Max {query_field}", 
                                       value=float("inf") if field_type == float else int(1e9),
                                       step=1 if field_type == int else 0.1)
        return {query_field: {"$gte": min_value, "$lte": max_value}}
    
    query_value = st.text_input(f"Value for {query_field}")
    return {query_field: query_value} if query_value else {}

def render_view_edit_tab(collection, collection_name):
    """View and edit data tab"""
    st.header("View and Edit Data")
    
    # Initialize session state for data persistence
    if "loaded_data" not in st.session_state:
        st.session_state.loaded_data = None
    
    # Query builder
    st.subheader("Query Options")
    sample_doc = collection.find_one({}, {"_id": 0})
    fields = ["No Filter"] + list(sample_doc.keys()) if sample_doc else ["No Filter"]
    query_field = st.selectbox("Filter by Field", fields)
    query = build_query(collection, query_field)
    
    limit = st.slider("Number of records to display", 5, 2000, 20)
    
    if st.button("Load Data"):
        try:
            # Fetch and display data
            data = [convert_doc_for_display(doc) for doc in collection.find(query).limit(limit)]
            
            if not data:
                st.warning("No data found matching your criteria")
                st.session_state.loaded_data = None
                return
            
            df = pd.DataFrame(data)
            st.session_state.loaded_data = df
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.loaded_data = None
    
    # Display data if it exists in session state
    if st.session_state.loaded_data is not None:
        df = st.session_state.loaded_data
        st.dataframe(df)
        
        # Export functionality
        export_format = st.selectbox("Export Format", ["CSV", "JSON"], key="export_format")
        if st.button("Export Data"):
            if export_format == "CSV":
                st.download_button(
                    "Download CSV",
                    df.to_csv(index=False),
                    f"{collection_name}_export.csv",
                    "text/csv"
                )
            else:
                st.download_button(
                    "Download JSON",
                    df.to_json(orient="records", date_format="iso"),
                    f"{collection_name}_export.json",
                    "application/json"
                )
        
        # Record editing
        render_record_editor(collection, df)

def render_record_editor(collection, df):
    """Render record editing form"""
    st.subheader("Edit Record")
    
    # Create more readable labels for the selectbox
    # Show first few columns of data along with index
    if len(df) == 0:
        st.info("No records loaded")
        return
    
    # Get first 3 non-id columns to display as preview
    display_cols = [col for col in df.columns if col != "_id"][:3]
    record_options = {}
    
    for idx, row in df.iterrows():
        preview = " | ".join([f"{col}: {str(row[col])[:20]}" for col in display_cols])
        label = f"Record {idx + 1}: {preview}"
        record_options[label] = row["_id"]
    
    selected_label = st.selectbox("Select Record to Edit", list(record_options.keys()), key="record_edit_select")
    
    if not selected_label:
        return
    
    record_id = record_options[selected_label]
    selected_record = df[df["_id"] == record_id].iloc[0].to_dict()
    
    with st.form("edit_record_form"):
        edited_record = {
            key: st.text_input(f"Edit {key}", value=value, key=f"edit_{key}")
            for key, value in selected_record.items()
            if key != "_id"
        }
        
        if st.form_submit_button("Update Record"):
            try:
                result = collection.update_one({"_id": record_id}, {"$set": edited_record})
                st.success("Record updated" if result.modified_count > 0 else "No changes made")
            except Exception as e:
                st.error(f"Error updating record: {e}")
    
    if st.button("Delete Record", key="delete_record_btn"):
        try:
            result = collection.delete_one({"_id": record_id})
            st.success("Record deleted" if result.deleted_count > 0 else "Failed to delete")
        except Exception as e:
            st.error(f"Error deleting record: {e}")

def render_schema_tab(collection):
    """Schema management tab"""
    st.header("Schema Management")
    
    sample_doc = collection.find_one({}, {"_id": 0})
    if not sample_doc:
        st.warning("No data found in collection. Import data first.")
        return
    
    # Display current schema
    st.subheader("Current Fields")
    schema_df = pd.DataFrame([
        {"Field": field, "Type": type(value).__name__, "Sample": str(value)[:50]}
        for field, value in sample_doc.items()
    ])
    st.dataframe(schema_df)
    
    fields = list(sample_doc.keys())
    
    # Schema operations
    st.subheader("Schema Operations")
    render_rename_field(collection, fields)
    render_add_field(collection)
    render_remove_field(collection, fields)
    render_index_management(collection, fields)

def render_rename_field(collection, fields):
    """Render rename field UI"""
    with st.expander("Rename Field"):
        field_to_rename = st.selectbox("Select Field to Rename", fields, key="rename_field_select")
        new_field_name = st.text_input("New Field Name", key="rename_field_input")
        
        if st.button("Rename Field") and new_field_name:
            try:
                collection.update_many({}, {"$rename": {field_to_rename: new_field_name}})
                st.success(f"Field '{field_to_rename}' renamed to '{new_field_name}'")
            except Exception as e:
                st.error(f"Error renaming field: {e}")

def render_add_field(collection):
    """Render add field UI"""
    with st.expander("Add New Field"):
        new_field = st.text_input("New Field Name", key="add_field_name")
        default_value = st.text_input("Default Value", key="add_field_default")
        
        if st.button("Add Field") and new_field:
            try:
                # Try to convert to appropriate type
                for converter in [int, float]:
                    try:
                        default_value = converter(default_value)
                        break
                    except ValueError:
                        continue
                
                collection.update_many({}, {"$set": {new_field: default_value}})
                st.success(f"Field '{new_field}' added successfully")
            except Exception as e:
                st.error(f"Error adding field: {e}")

def render_remove_field(collection, fields):
    """Render remove field UI"""
    with st.expander("Remove Field"):
        field_to_remove = st.selectbox("Select Field to Remove", fields, key="remove_field")
        
        if st.button("Remove Field") and st.checkbox("Confirm Removal"):
            try:
                collection.update_many({}, {"$unset": {field_to_remove: ""}})
                st.success(f"Field '{field_to_remove}' removed successfully")
            except Exception as e:
                st.error(f"Error removing field: {e}")

def render_index_management(collection, fields):
    """Render index management UI"""
    with st.expander("Manage Indexes"):
        st.subheader("Current Indexes")
        indexes = list(collection.list_indexes())
        index_df = pd.DataFrame([
            {"Name": idx["name"], "Fields": str(idx["key"]), "Unique": idx.get("unique", False)}
            for idx in indexes
        ])
        st.dataframe(index_df)
        
        st.subheader("Create New Index")
        index_field = st.selectbox("Field to Index", fields, key="index_field_select")
        index_unique = st.checkbox("Unique Index", key="index_unique_check")
        
        if st.button("Create Index"):
            try:
                collection.create_index([(index_field, pymongo.ASCENDING)], unique=index_unique)
                st.success(f"Index created on '{index_field}'")
            except Exception as e:
                st.error(f"Error creating index: {e}")

# ============= Main App =============
def main():
    st.title("Pennsylvania Child Protection Clearances")
    #st.subheader("Import, Store, and Manage CSV Data")
    
    client = init_connection()
    if not client:
        st.error("Failed to connect to MongoDB. Please check your connection.")
        return
    
    collection, collection_name, db_name = get_or_create_collection(client, st.sidebar)
    if collection is None:
        return
    
    # About
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    This application allows you to import CSV files of temple workers exported into a database, manage the data with full Create, Read, Update and Delete capabilities, 
    and customize the schema by renaming or adding fields. You can also overwrite the whole collection using a new csv file. 
    Reports can be sorted by all fields using the buttons above the columns.
    """)
    
    # Render tabs
    tabs = st.tabs(["Import CSV", "View/Edit Data", "Schema Management"])
    
    with tabs[0]:
        render_import_tab(collection)
    
    with tabs[1]:
        render_view_edit_tab(collection, collection_name)
    
    with tabs[2]:
        render_schema_tab(collection)
    
    # Reports
    render_report_builder(client, db_name, collection_name)

if __name__ == "__main__":
    main()