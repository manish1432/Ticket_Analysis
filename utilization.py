import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_utilization_data(start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
   
    query = """
        SELECT Assignee, SUM(TimeSpent) AS TotalTimeSpent
        FROM ServiceDesk
    """
   
    dates = []
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date
       
        # Exclude weekends (Saturday and Sunday)
        dates = [start + timedelta(days=i) for i in range((end - start).days) if (start + timedelta(days=i)).weekday() < 5]
        if dates:
            formatted_start_date = dates[0].strftime("%Y-%m-%d")
            formatted_end_date = dates[-1].strftime("%Y-%m-%d")
            query += f" WHERE Created BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"
   
    query += """
        GROUP BY Assignee
        ORDER BY TotalTimeSpent DESC;
    """
   
    df = pd.read_sql_query(query, conn)
    conn.close()
   
    # Convert TotalTimeSpent from seconds to hours
    df['TotalTimeSpentHours'] = df['TotalTimeSpent'] / 3600
   
    if dates:
        # Calculate the total available work hours (5 days a week * 8 hours per day)
        total_days = len(dates)
        available_work_hours = total_days * 8  # 8 hours per day
    else:
        available_work_hours = 1  # Avoid division by zero if no dates are provided
 
    # Calculate the utilization percentage based on available work hours
    df['UtilizationPercentage'] = (df['TotalTimeSpentHours'] / available_work_hours) * 100
   
    # Ensure Percentage is always defined
    df['Percentage'] = df['UtilizationPercentage'].fillna(0)
   
    return df


# Function to fetch breakdown data by TriagedBusiness for a specific engineer
def fetch_breakdown_data(assignee, start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    query = f"""
        SELECT TriagedBusiness, COUNT(*) AS IssueCount
        FROM ServiceDesk
        WHERE Assignee = '{assignee}'
    """
    
    # Add date range filter to the query if provided
    if start_date and end_date:
        query += f" AND Created BETWEEN '{start_date}' AND '{end_date}'"
    
    query += """
        GROUP BY TriagedBusiness
        ORDER BY IssueCount DESC;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

# @app.route('/', methods=['GET', 'POST'])
def get_data(start_date, end_date):
    # start_date = request.form.get('start_date')
    # end_date = request.form.get('end_date')
    
    # Fetch utilization data based on the selected date range
    data = fetch_utilization_data(start_date, end_date)

    # Calculate total time spent for percentage calculation
    total_time_spent = data['TotalTimeSpent'].sum()

    # Create a Plotly bar chart
    fig = px.bar(data, x='Assignee', y='TotalTimeSpentHours',
                 title='Engineer Utilization',
                 labels={'Assignee': 'Engineer Name', 'TotalTimeSpentHours': 'Total Utilization (hours)'},
                 text='UtilizationPercentage',
                 hover_data={'UtilizationPercentage': ':.2f'})

    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title='Total Time Spent (hours)')

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    # Convert data to dict for table rendering
    table_data = data.to_dict('records')

    # Prepare date range label
    date_range_label = f"Data from {start_date} to {end_date}" if start_date and end_date else "All Data"

    return render_template('utilization.html', graph_json=graph_json, table_data=table_data, date_range_label=date_range_label, start_date=start_date, end_date=end_date)

@app.route('/breakdown/<assignee>')
def breakdown(assignee):
    # Get date range from request args
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Fetch breakdown data for the selected engineer
    breakdown_data = fetch_breakdown_data(assignee, start_date, end_date)

    # Convert breakdown data to a dictionary for JSON response
    breakdown_dict = breakdown_data.to_dict('records')

    return jsonify(breakdown_dict)

if __name__ == '__main__':
    app.run(debug=True)
