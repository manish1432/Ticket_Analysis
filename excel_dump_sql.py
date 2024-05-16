import pandas as pd
import sqlite3
from pathlib import Path

def excel_to_sqlite(excel_file, sqlite_db):
    # Read data from Excel file into a pandas DataFrame
    df = pd.read_excel(excel_file)

    # Create SQLite connection and cursor
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()

    # Extract filename without extension from the Excel file path
    excel_path = Path(excel_file)
    table_name = excel_path.stem  # Get filename without extension

    # Create a SQLite table based on DataFrame columns
    columns = ', '.join(f'"{col}" TEXT' for col in df.columns)  # Assuming all columns as TEXT for simplicity
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})'
    cursor.execute(create_table_sql)

    # Insert data into SQLite table row by row
    for _, row in df.iterrows():
        values = ', '.join(f'"{str(value).replace("\"", "\"\"")}"' for value in row)  # Handle double quotes in values
        insert_sql = f'INSERT INTO "{table_name}" VALUES ({values})'
        try:
            cursor.execute(insert_sql)
        except sqlite3.Error as e:
            print(f"Error inserting row into SQLite table: {e}")
            print(f"Insert SQL: {insert_sql}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print(f"Data imported from '{excel_file}' to '{sqlite_db}' in table '{table_name}'.")

if __name__ == '__main__':
    # Specify file paths using raw string literals (r"...")
    excel_file_path = r"C:\Users\tiwarim\Downloads\Power_BI_TCS_IO\ServiceDesk.xlsx"
    sqlite_db_path = r"C:\Users\tiwarim\Downloads\Power_BI_TCS_IO\io_database.db"

    # Call the function to import data from Excel to SQLite
    excel_to_sqlite(excel_file_path, sqlite_db_path)
