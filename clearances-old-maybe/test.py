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
    df["Personal Phone"] = df["Personal Phone"].apply(normalize_phone)
    df["Email"] = df["Email"].apply(normalize_email)

    # --- HTML RENDERING ---
    display_df = df.copy()
    display_df["Personal Phone"] = display_df["Personal Phone"].apply(
        lambda v: f"{v}{copy_button(v)}"
    )
    display_df["Email"] = display_df["Email"].apply(
        lambda v: f"{v}{copy_button(v)}"
    )
    display_df["Skills"] = display_df["Skills"].apply(render_skill_badges)

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
