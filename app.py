import streamlit as st  # pyright: ignore[reportMissingImports]
import pandas as pd
from datetime import date

st.set_page_config(layout="wide")

st.title("👨‍Attendance Management System")

# Initialize session state for students and attendance
if 'students' not in st.session_state:
    st.session_state['students'] = pd.DataFrame(columns=['ID', 'Name', 'Year', 'Branch'])
if 'attendance' not in st.session_state:
    st.session_state['attendance'] = {}

# --- Date Selection ---
st.header("1. Select Date")
selected_date = st.date_input("Select Date", date.today())
st.session_state['selected_date'] = selected_date

# --- Mark Attendance ---
st.header("2. Mark Attendance")

if not st.session_state['students'].empty:
    current_date_attendance = st.session_state['attendance'].get(selected_date, {})
    updated_attendance = {}

    attendance_data = []
    for index, student in st.session_state['students'].iterrows():
        student_id = student['ID']
        student_name = student['Name']
        # Default to previous attendance or Present if not set
        status = current_date_attendance.get(student_id, True) # True for Present, False for Absent
        attendance_data.append({'ID': student_id, 'Name': student_name, 'Present': status})
    
    attendance_df = pd.DataFrame(attendance_data)

    # Display editable dataframe for attendance
    edited_attendance_df = st.data_editor(
        attendance_df,
        column_config={
            "ID": st.column_config.Column("ID", width="small", disabled=True),
            "Name": st.column_config.Column("Name", width="large", disabled=True),
            "Present": st.column_config.CheckboxColumn("Present", default=True)
        },
        hide_index=True,
        num_rows="dynamic"
    )

    if st.button("Save Attendance"):
        for index, row in edited_attendance_df.iterrows():
            updated_attendance[row['ID']] = row['Present']
        st.session_state['attendance'][selected_date] = updated_attendance
        st.success(f"Attendance for {selected_date} saved successfully!")
else:
    st.info("No students added yet. Please add students in the 'Manage Students' section.")

# --- Manage Students ---
st.header("3. Manage Students")

with st.expander("Add New Student"):
    with st.form("add_student_form", clear_on_submit=True):
        new_student_name = st.text_input("Student Name")
        new_student_year = st.selectbox("Year", ["FE", "SE", "TE", "BE"])
        new_student_branch = st.text_input("Branch")
        add_student_submitted = st.form_submit_button("Add Student")

        if add_student_submitted and new_student_name:
            new_id = len(st.session_state['students']) + 1
            new_student_data = pd.DataFrame([{'ID': new_id, 'Name': new_student_name, 'Year': new_student_year, 'Branch': new_student_branch}])
            st.session_state['students'] = pd.concat([st.session_state['students'], new_student_data], ignore_index=True)
            st.success(f"Student {new_student_name} added successfully!")

st.subheader("Current Students")
if not st.session_state['students'].empty:
    st.dataframe(st.session_state['students'], use_container_width=True)

    students_to_delete = st.multiselect("Select students to delete", st.session_state['students']['Name'].tolist())
    if st.button("Delete Selected Students"):
        st.session_state['students'] = st.session_state['students'][~st.session_state['students']['Name'].isin(students_to_delete)]
        st.success(f"Deleted {len(students_to_delete)} student(s).")
        # Also remove their attendance records if any
        for date_key in st.session_state['attendance']:
            st.session_state['attendance'][date_key] = { 
                k: v for k, v in st.session_state['attendance'][date_key].items() 
                if k in st.session_state['students']['ID'].tolist() # only keep attendance for existing student IDs
            }
else:
    st.info("No students added yet.")

# --- Download Attendance Data ---
st.header("4. Download Attendance Data")

if st.session_state['attendance'] and not st.session_state['students'].empty:
    # Create a list to store attendance records in a flat format
    all_attendance_records = []

    for selected_date_str, daily_attendance in st.session_state['attendance'].items():
        for student_id, status in daily_attendance.items():
            all_attendance_records.append({
                'Date': selected_date_str,
                'ID': student_id,
                'Status': 'Present' if status else 'Absent'
            })

    if all_attendance_records:
        attendance_df_flat = pd.DataFrame(all_attendance_records)

        # Merge with student details
        full_attendance_df = pd.merge(
            attendance_df_flat,
            st.session_state['students'],
            on='ID',
            how='left'
        )
        
        # Reorder columns for better readability
        full_attendance_df = full_attendance_df[['Date', 'ID', 'Name', 'Year', 'Branch', 'Status']]
        
        st.dataframe(full_attendance_df, use_container_width=True)

        csv = full_attendance_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Attendance as CSV",
            data=csv,
            file_name="attendance_record.csv",
            mime="text/csv",
        )
    else:
        st.info("No attendance records to display or download yet.")
else:
    st.info("No attendance data or student data available to download.")
