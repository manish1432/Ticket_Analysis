import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime

app = Flask(__name__)

# Function to fetch ticket data based on date range
def fetch_ticket_data(start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    query = """
        SELECT Assignee,
               COUNT(*) AS TicketCount,
               SUM(CASE WHEN ServiceIssue = 'self-ticket' THEN 1 ELSE 0 END) AS SelfTicketCount
        FROM ServiceDesk
    """
    
    if start_date and end_date:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        query += f" WHERE Created BETWEEN '{start_date_str}' AND '{end_date_str}'"
    
    query += " GROUP BY Assignee ORDER BY TicketCount DESC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

# Function to fetch service issue breakdown for a specific engineer
def fetch_engineer_details(engineer_name):
    conn = sqlite3.connect('io_database.db')
    
    query = """
        SELECT ServiceIssue, COUNT(*) AS IssueCount
        FROM ServiceDesk
        WHERE Assignee = ?
        GROUP BY ServiceIssue
    """
    
    df = pd.read_sql_query(query, conn, params=(engineer_name,))
    conn.close()
    
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    date_range_label = ""
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            date_range_label = f"Data from {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
    
    # Fetch ticket data based on the selected date range
    ticket_data = fetch_ticket_data(start_date, end_date)
    
    # Sort ticket data by TicketCount in descending order
    ticket_data_sorted = ticket_data.sort_values(by='TicketCount', ascending=False)
    
    # Convert ticket_data_sorted to a list of dictionaries
    engineers_data = ticket_data_sorted.to_dict('records')
    
    # Create Plotly bar chart
    fig = px.bar(ticket_data_sorted, x='TicketCount', y='Assignee',
                 labels={'TicketCount': 'Ticket Count', 'Assignee': 'Engineer'},
                 title='Tickets Assigned to Engineers')
    
    # Customize layout
    fig.update_layout(
        plot_bgcolor='#f8f9fa',  # Light gray plot background
        paper_bgcolor='#f8f9fa',  # Light gray paper background
        font_family='Arial',  # Set font family
        font_color='#333',  # Set font color
        title_font_size=24,  # Title font size
        xaxis_title_font_size=22,  # X-axis title font size
        yaxis_title_font_size=22,  # Y-axis title font size
        margin=dict(l=150, r=50, t=80, b=50),  # Adjust margins
        height=400,  # Set chart height to 400 pixels
        bargap=0.2,  # Gap between bars
        bargroupgap=0.1,  # Gap between bar groups
        xaxis_showgrid=True,  # Show gridlines on x-axis
        yaxis_tickfont_size=18,  # Y-axis tick font size
        xaxis_tickfont_size=18,  # X-axis tick font size
        showlegend=False  # Hide legend
    )

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    return render_template('engineer.html', graph_json=graph_json,
                           engineers_data=engineers_data, date_range_label=date_range_label)

@app.route('/engineer-details', methods=['POST'])
def engineer_details():
    data = request.get_json()
    engineer_name = data['engineerName']
    
    # Fetch engineer details
    details_df = fetch_engineer_details(engineer_name)
    details_dict = details_df.set_index('ServiceIssue')['IssueCount'].to_dict()
    
    return jsonify(details={'engineerName': engineer_name, 'details': details_dict})

if __name__ == '__main__':
    app.run(debug=True)
