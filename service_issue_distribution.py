import os
import logging
from flask import Flask, render_template, request
import sqlite3
import plotly
import plotly.graph_objs as go
from datetime import datetime

app = Flask(__name__)

def fetch_service_issue_counts(start_date=None, end_date=None):
    try:
        conn = sqlite3.connect('io_database.db')
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM ServiceDesk WHERE ServiceIssue = ?"
        params = []

        if start_date and end_date:
            query += " AND Created BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        alerts_count = cursor.execute(query, ('Alerts',) + tuple(params)).fetchone()[0]
        request_count = cursor.execute(query, ('Request',) + tuple(params)).fetchone()[0]
        self_ticket_count = cursor.execute(query, ('Self-Ticket',) + tuple(params)).fetchone()[0]

        conn.close()

        return alerts_count, request_count, self_ticket_count

    except Exception as e:
        logging.error(f"Error fetching service issue counts: {str(e)}")
        raise

def fetch_triaged_business_counts(start_date=None, end_date=None):
    try:
        conn = sqlite3.connect('io_database.db')
        cursor = conn.cursor()

        query = """
            SELECT TriagedBusiness,
                SUM(CASE WHEN ServiceIssue = 'Alerts' THEN 1 ELSE 0 END) AS Alerts_Count,
                SUM(CASE WHEN ServiceIssue = 'Request' THEN 1 ELSE 0 END) AS Request_Count,
                SUM(CASE WHEN ServiceIssue = 'Self-Ticket' THEN 1 ELSE 0 END) AS Self_Ticket_Count
            FROM ServiceDesk
            WHERE TriagedBusiness IN ('The Mill', 'MPC', 'Technicolor Games', 'Mikros Animation')
        """

        params = []
        if start_date and end_date:
            query += " AND Created BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        query += " GROUP BY TriagedBusiness"
        cursor.execute(query, tuple(params))

        results = cursor.fetchall()
        conn.close()

        return results

    except Exception as e:
        logging.error(f"Error fetching triaged business counts: {str(e)}")
        raise

def generate_pie_chart(labels, values, title):
    trace = go.Pie(
        labels=labels,
        values=values,
        hoverinfo='label+percent+value',
        textinfo='label+percent',
        textfont=dict(size=14),
        marker=dict(colors=plotly.colors.DEFAULT_PLOTLY_COLORS),
        hole=0.4
    )

    layout = go.Layout(
        title=title,
        titlefont=dict(size=24),
        margin=dict(l=30, r=30, t=60, b=30),
        legend=dict(font=dict(size=14)),
        transition=dict(duration=1000, easing='cubic-in-out')
    )

    fig = go.Figure(data=[trace], layout=layout)
    chart_json = fig.to_json()

    return chart_json

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        start_date = None
        end_date = None
        
        if request.method == 'POST':
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        alerts_count, request_count, self_ticket_count = fetch_service_issue_counts(start_date, end_date)

        # Generate Pie chart for Service Issue Distribution
        labels = ['Alerts', 'Request', 'Self-Ticket']
        values = [alerts_count, request_count, self_ticket_count]
        service_issue_chart_json = generate_pie_chart(labels, values, 'Service Issue Distribution')

        # Generate Pie charts for Triaged Business
        triaged_business_data = fetch_triaged_business_counts(start_date, end_date)
        triaged_labels = [item[0] for item in triaged_business_data]
        triaged_alerts = [item[1] for item in triaged_business_data]
        triaged_requests = [item[2] for item in triaged_business_data]
        triaged_self_tickets = [item[3] for item in triaged_business_data]

        triaged_alerts_chart_json = generate_pie_chart(triaged_labels, triaged_alerts, 'Triaged Business Alerts')
        triaged_requests_chart_json = generate_pie_chart(triaged_labels, triaged_requests, 'Triaged Business Requests')
        triaged_self_tickets_chart_json = generate_pie_chart(triaged_labels, triaged_self_tickets, 'Triaged Business Self-Tickets')

        # Prepare date range string
        date_range = f"Showing data from {start_date} to {end_date}" if start_date and end_date else "Showing all available data"

        return render_template('service_issue_distribution.html', service_issue_chart_json=service_issue_chart_json,
                               triaged_alerts_chart_json=triaged_alerts_chart_json,
                               triaged_requests_chart_json=triaged_requests_chart_json,
                               triaged_self_tickets_chart_json=triaged_self_tickets_chart_json,
                               alerts_count=alerts_count, request_count=request_count,
                               self_ticket_count=self_ticket_count, date_range=date_range)

    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        return render_template('error.html', error_message=str(e))

if __name__ == '__main__':
    logging.basicConfig(filename='app.log', level=logging.INFO)
    app.run(debug=True)
