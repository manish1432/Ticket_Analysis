import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px


app = Flask(__name__)

# Function to fetch SLA data based on date range
def fetch_sla_data(start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    query = "SELECT SLA, COUNT(*) AS Count FROM ServiceDesk"
    
    if start_date and end_date:
        query += f" WHERE Created BETWEEN '{start_date}' AND '{end_date}'"
    
    query += " GROUP BY SLA"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to fetch breakdown data based on SLA, TriagedBusiness, and date range
def fetch_breakdown_data(sla, start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    query = """
        SELECT TriagedBusiness, COUNT(*) AS Count
        FROM ServiceDesk
        WHERE SLA = ?
    """
    
    if start_date and end_date:
        query += f" AND Created BETWEEN '{start_date}' AND '{end_date}'"
    
    query += " GROUP BY TriagedBusiness"
    
    df = pd.read_sql_query(query, conn, params=[sla])
    conn.close()
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        breakdown_sla = request.form.get('breakdown_sla')
    else:
        start_date = None
        end_date = None
        breakdown_sla = None
    
    # Fetch SLA data based on date range
    sla_data = fetch_sla_data(start_date, end_date)
    
    # Create Plotly donut pie chart
    fig = px.pie(sla_data, values='Count', names='SLA', title='SLA Distribution', hole=0.4)
    graph_json = fig.to_json()

    # Convert SLA data to a dictionary for table rendering
    sla_table_data = sla_data.to_dict('records')

    # Fetch breakdown data if SLA is provided
    breakdown_data = None
    if breakdown_sla:
        breakdown_data = fetch_breakdown_data(breakdown_sla, start_date, end_date)

    return render_template('sla.html', graph_json=graph_json, sla_table_data=sla_table_data,
                           breakdown_data=breakdown_data, start_date=start_date, end_date=end_date)

@app.route('/breakdown', methods=['POST'])
def breakdown():
    sla = request.json['sla']
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    breakdown_data = fetch_breakdown_data(sla, start_date, end_date)
    breakdown_html = breakdown_data.to_html(classes='table table-striped table-bordered', index=False)
    return breakdown_html

if __name__ == '__main__':
    app.run(debug=True)
