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

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Issue Distribution by Triaged Business</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <style>
        body {
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            text-align: center;
            margin-top: 20px;
            color: #343a40;
        }
        .form-row {
            margin-top: 20px;
        }
        .btn-primary {
            width: 100%;
            transition: background-color 0.3s ease;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        #ticketChart {
            margin-top: 30px;
        }
        .table-responsive {
            margin-top: 20px;
        }
        .table {
            animation: fadeIn 1s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ticket Analysis by Business Unit</h1>
        
        <!-- Date range selection form -->
        <form method="POST" action="/">
            <div class="form-row">
                <div class="col">
                    <input type="date" class="form-control" name="start_date" placeholder="Start Date">
                </div>
                <div class="col">
                    <input type="date" class="form-control" name="end_date" placeholder="End Date">
                </div>
                <div class="col">
                    <select class="form-control" name="triaged_business">
                        <option value="MPC">MPC</option>
                        <option value="The Mill">The Mill</option>
                        <option value="Technicolor Games">Technicolor Games</option>
                        <option value="Mikros Animation">Mikros Animation</option>
                        <option value="Technicolor Group">Technicolor Group (All)</option>
                    </select>
                </div>
                <div class="col">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-filter"></i> Apply Filter</button>
                </div>
            </div>
        </form>

        <!-- Display date range label -->
        {% if date_range_label %}
            <h2>{{ date_range_label }}</h2>
        {% endif %}

        <!-- Display total issues count -->
        <h3>Total Issues: {{ total_issues }}</h3>

        <!-- Display Plotly pie chart -->
        <div id="ticketChart"></div>

        <!-- Display issue counts -->
        <h3>Issue Counts</h3>
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead class="thead-dark">
                    <tr>
                        <th>Business Unit</th>
                        <th>Service Issue</th>
                        <th>Issue Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for issue in issues_data %}
                        <tr>
                            <td>{{ issue['TriagedBusiness'] }}</td>
                            <td>{{ issue['ServiceIssue'] }}</td>
                            <td>{{ issue['IssueCount'] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        $(document).ready(function() {
            // Display Plotly chart
            var graphJson = {{ graph_json|tojson|safe }};
            var figure = JSON.parse(graphJson);
            Plotly.newPlot('ticketChart', figure.data, figure.layout);
        });
    </script>

    <!-- Bootstrap and jQuery scripts -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
