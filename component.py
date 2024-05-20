import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime

app = Flask(__name__)

def fetch_data(start_date=None, end_date=None):
    # Connect to SQLite database
    conn = sqlite3.connect('io_database.db')

    # Construct the base SQL query
    query = "SELECT Component, COUNT(*) AS Count FROM ServiceDesk"

    # Append date filtering conditions if start_date and end_date are provided
    if start_date and end_date:
        start_date_str = start_date.strftime('%Y-%m-%d')  # Convert date to string
        end_date_str = end_date.strftime('%Y-%m-%d')      # Convert date to string
        query += f" WHERE Created BETWEEN '{start_date_str}' AND '{end_date_str}'"

    query += " GROUP BY Component"
    query += " ORDER BY Count DESC;"  # Sort by count in descending order

    # Fetch data using the SQL query
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Sort DataFrame by Count column in descending order
    df = df.sort_values(by='Count', ascending=False)

    return df

def fetch_component_details(component, start_date, end_date):
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('io_database.db')
        print(component, start_date, end_date)

        # Construct SQL query to fetch top 10 details for the selected component
        query = f"SELECT Detail1, COUNT(*) AS Count FROM ServiceDesk WHERE Component = ? "
        if start_date and end_date:
            query += " AND Created >= ? AND Created <= ?"
        query += " GROUP BY Detail1"
        query += " ORDER BY Count DESC"  # Sort by count in descending order
        query += " LIMIT 10;"  # Limit to top 10 details
        if start_date and end_date:
                df = pd.read_sql_query(query, conn, params=(component, start_date, end_date))
        else:
                df = pd.read_sql_query(query, conn, params=(component,))

        return df
    except Exception as e:
        print(f"Error fetching component details for {component}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame if error occurs
    finally:
        conn.close()

# @app.route('/component', methods=['GET', 'POST'])
def get_data():
    date_range_label = ""
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        # Retrieve form data (start_date and end_date)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        # print(start_date, end_date)
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            # print(start_date, end_date)
            date_range_label = f"Data from {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
    
    # Fetch data based on the selected date range
    df = fetch_data(start_date, end_date)

    # Calculate total number of components
    total_components = df['Count'].sum()

    # Create Plotly bar chart with horizontal orientation
    fig = px.bar(df, x='Count', y='Component', orientation='h', title='Service Desk Component Counts',
                 labels={'Count': 'Number of Incidents', 'Component': 'Service Components'},
                 color='Count', color_continuous_scale='Blues')

    # Customize layout
    fig.update_layout(
        plot_bgcolor='#f0f0f0',  # Light gray plot background
        paper_bgcolor='#f0f0f0',  # Light gray paper background
        font_family='Arial',  # Set font family
        font_color='#333',  # Set font color
        title_font_size=24,  # Title font size
        xaxis_title_font_size=16,  # X-axis title font size
        yaxis_title_font_size=16,  # Y-axis title font size
        legend_title_font_size=14,  # Legend title font size
        margin=dict(l=120, r=20, t=80, b=50),  # Adjust margins
        coloraxis_colorbar=dict(
            title='Incident Count',  # Colorbar title
            tickfont=dict(size=12),  # Colorbar tick font size
            title_font_size=14,  # Colorbar title font size
            len=0.7,  # Colorbar length
            thickness=15  # Colorbar thickness
        )
    )

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    # Get total count for each component
    component_totals = df.set_index('Component').to_dict()['Count']
    print(start_date, end_date)
    return render_template('component.html', graph_json=graph_json, total_components=total_components,
                           component_totals=component_totals, date_range_label=date_range_label, start_date=start_date, end_date=end_date)



if __name__ == '__main__':
    app.run(debug=True)
