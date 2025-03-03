import streamlit as st
import pandas as pd
from io import BytesIO

def merge_files(file1, file2, file3, selected_columns):
    # Read files (supporting CSV & Excel)
    df1 = pd.read_excel(file1, engine="openpyxl") if file1.name.endswith('.xlsx') else pd.read_csv(file1)
    df2 = pd.read_excel(file2, engine="openpyxl") if file2.name.endswith('.xlsx') else pd.read_csv(file2)
    df3 = pd.read_excel(file3, engine="openpyxl") if file3.name.endswith('.xlsx') else pd.read_csv(file3)
    
    # Merge files based on 'Employee ID'
    merged_df = df1.merge(df3, on='Employee ID', how='left').merge(df2, on='Employee ID', how='left')
    
    # Filter only selected columns
    merged_df = merged_df[['Employee ID'] + selected_columns]
    
    # Drop duplicate PDF Reference Numbers per employee
    if 'PDF Reference Number' in merged_df.columns:
        merged_df = merged_df.drop_duplicates(subset=['Employee ID', 'PDF Reference Number'])
    
    # Generate a unique row number for each certificate per employee
    merged_df['Cert_Index'] = merged_df.groupby('Employee ID').cumcount() + 1
    
    # Pivot to ensure each employee has a single row
    final_df = merged_df.pivot(index='Employee ID', columns='Cert_Index', values=selected_columns)
    
    # Flatten multi-level column names
    final_df.columns = [f'{col[0]}_{col[1]}' for col in final_df.columns]
    
    # Reset index to make 'Employee ID' a column again
    final_df = final_df.reset_index()
    
    # Reorder columns in sequence
    column_order = ['Employee ID']
    max_cert_index = merged_df['Cert_Index'].max()  # Get max Cert_Index value
    for i in range(1, max_cert_index + 1):
        for col in selected_columns:
            column_order.append(f'{col}_{i}')
    
    # Keep only existing columns
    column_order = [col for col in column_order if col in final_df.columns]
    
    # Reorder DataFrame
    final_df = final_df[column_order]
    
    return final_df

# Streamlit UI
st.title("File Merger & Pivot Tool")

uploaded_files = st.file_uploader("Upload 3 files", accept_multiple_files=True, type=["csv", "xls", "xlsx"])

if uploaded_files and len(uploaded_files) == 3:
    file1, file2, file3 = uploaded_files
    
    # Read columns from the three files
    df1 = pd.read_excel(file1, engine="openpyxl") if file1.name.endswith('.xlsx') else pd.read_csv(file1)
    df2 = pd.read_excel(file2, engine="openpyxl") if file2.name.endswith('.xlsx') else pd.read_csv(file2)
    df3 = pd.read_excel(file3, engine="openpyxl") if file3.name.endswith('.xlsx') else pd.read_csv(file3)
    
    all_columns = list(set(df1.columns.tolist() + df2.columns.tolist() + df3.columns.tolist()))
    
    # Multi-select for columns
    selected_columns = st.multiselect("Choose Columns to Process", all_columns, default=[])
    
    if selected_columns:
        merged_output = merge_files(file1, file2, file3, selected_columns)
        
        # Display merged output
        st.write("### Merged & Processed Output")
        st.dataframe(merged_output)
        
        # Create an in-memory Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            merged_output.to_excel(writer, index=False)
        
        output.seek(0)  # Move cursor to start
        
        # Download button
        st.download_button(
            label="Download Processed File",
            data=output,
            file_name="merged_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
