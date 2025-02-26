import streamlit as st
import pandas as pd
import io

def merge_files(file1, file2, file3, selected_columns):
    # Function to read any file format (CSV or Excel)
    def read_file(file):
        return pd.read_excel(file) if file.name.endswith(('.xls', '.xlsx')) else pd.read_csv(file)

    # Read files
    df1, df2, df3 = read_file(file1), read_file(file2), read_file(file3)

    # Ensure 'Employee ID' exists in all files
    for df, file in zip([df1, df2, df3], [file1, file2, file3]):
        if "Employee ID" not in df.columns:
            st.error(f"Error: 'Employee ID' not found in {file.name}")
            return None

    # Merge files based on 'Employee ID'
    merged_df = df1.merge(df3, on='Employee ID', how='left').merge(df2, on='Employee ID', how='left')

    # Validate selected columns
    valid_columns = [col for col in selected_columns if col in merged_df.columns]
    if not valid_columns:
        st.error("Error: No valid columns selected for processing!")
        return None

    # Keep only required columns
    merged_df = merged_df[['Employee ID'] + valid_columns]

    # Remove duplicate 'PDF Reference Number' per employee
    if 'PDF Reference Number' in merged_df.columns:
        merged_df = merged_df.drop_duplicates(subset=['Employee ID', 'PDF Reference Number'])

    # Generate row number per certificate per employee
    merged_df['Cert_Index'] = merged_df.groupby('Employee ID').cumcount() + 1

    # Pivot to ensure each employee has a single row
    final_df = merged_df.pivot(index='Employee ID', columns='Cert_Index', values=valid_columns)

    # Flatten multi-level column names
    final_df.columns = [f'{col[0]}_{col[1]}' for col in final_df.columns]

    # Reset index
    final_df = final_df.reset_index()

    # Reorder columns dynamically
    column_order = ['Employee ID']
    max_cert_index = merged_df['Cert_Index'].max()
    
    for i in range(1, max_cert_index + 1):
        for col in valid_columns:
            column_order.append(f'{col}_{i}')
    
    # Ensure only existing columns are included
    column_order = [col for col in column_order if col in final_df.columns]
    final_df = final_df[column_order]

    return final_df

# Streamlit UI
st.title("📂 File Merger & Pivot Tool")

uploaded_files = st.file_uploader("📌 Upload 3 files (CSV/Excel)", accept_multiple_files=True, type=["csv", "xls", "xlsx"])

if uploaded_files and len(uploaded_files) == 3:
    file1, file2, file3 = uploaded_files

    # Read all columns from uploaded files
    def read_columns(file):
        df = pd.read_excel(file) if file.name.endswith(('.xls', '.xlsx')) else pd.read_csv(file)
        return list(df.columns)

    all_columns = list(set(read_columns(file1) + read_columns(file2) + read_columns(file3)))
    selected_columns = st.multiselect("🛠 Choose Columns to Process", all_columns, default=all_columns)

    if selected_columns:
        merged_output = merge_files(file1, file2, file3, selected_columns)

        if merged_output is not None:
            # Display the merged DataFrame
            st.write("### ✅ Merged & Processed Output")
            st.dataframe(merged_output)

            # Convert DataFrame to Excel (in-memory)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                merged_output.to_excel(writer, index=False, sheet_name="Merged Data")

            # Download button
            st.download_button(
                label="📥 Download Processed File",
                data=output.getvalue(),
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
