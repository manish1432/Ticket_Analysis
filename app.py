import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime

app = Flask(__name__)

# Function to fetch ticket data based on date range and triaged business
def fetch_ticket_data(triaged_business, start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    if triaged_business == "Technicolor Group":
        query = """
            SELECT TriagedBusiness,
                   ServiceIssue,
                   COUNT(*) AS IssueCount
            FROM ServiceDesk
            WHERE TriagedBusiness IN ('MPC', 'The Mill', 'Technicolor Games', 'Mikros Animation')
        """
        params = []
    else:
        query = """
            SELECT TriagedBusiness,
                   ServiceIssue,
                   COUNT(*) AS IssueCount
            FROM ServiceDesk
            WHERE TriagedBusiness = ?
        """
        params = [triaged_business]
    
    if start_date and end_date:
        query += " AND Created BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    
    query += " GROUP BY TriagedBusiness, ServiceIssue ORDER BY IssueCount DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    triaged_business = request.form.get('triaged_business', 'MPC')  # Default triaged business
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    # Fetch ticket data based on triaged business and date range
    data = fetch_ticket_data(triaged_business, start_date, end_date)
    
    if triaged_business == "Technicolor Group":
        title = "Issue Distribution for Technicolor Group"
        fig = px.sunburst(data, path=['TriagedBusiness', 'ServiceIssue'], values='IssueCount',
                          title=title, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textinfo='label+percent root')
    else:
        title = f"Issue Distribution for {triaged_business}"
        fig = px.pie(data, values='IssueCount', names='ServiceIssue', title=title,
                     color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
        fig.update_traces(textinfo='percent+label', hoverinfo='label+percent+value')
    
    fig.update_layout(
        title_font_size=24,
        title_font_family='Arial',
        showlegend=True,
        legend_title='Service Issues',
        legend=dict(font=dict(size=12)),
        paper_bgcolor='#f8f9fa',
        plot_bgcolor='#f8f9fa',
    )

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    # Prepare date range label and total issues count
    date_range_label = ""
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        date_range_label = f"Data from {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
    
    total_issues = data['IssueCount'].sum()

    issues_data = data.to_dict('records')

    return render_template('index.html', graph_json=graph_json, 
                           triaged_business=triaged_business, 
                           date_range_label=date_range_label, 
                           total_issues=total_issues, 
                           issues_data=issues_data)

if __name__ == '__main__':
    app.run(debug=True)
