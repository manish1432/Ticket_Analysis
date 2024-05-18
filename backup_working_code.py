#service_distribution
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

        return render_template('index.html', service_issue_chart_json=service_issue_chart_json,
                               triaged_alerts_chart_json=triaged_alerts_chart_json,
                               triaged_requests_chart_json=triaged_requests_chart_json,
                               triaged_self_tickets_chart_json=triaged_self_tickets_chart_json,
                               alerts_count=alerts_count, request_count=request_count,
                               self_ticket_count=self_ticket_count)

    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        return render_template('error.html', error_message=str(e))

if __name__ == '__main__':
    logging.basicConfig(filename='app.log', level=logging.INFO)
    app.run(debug=True)


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Issue Distribution</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f8f9fa;
            color: #333333;
        }
        .container {
            max-width: 800px;
            margin: auto;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background-color: #ffffff;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #007bff;
        }
        .plotly-chart {
            text-align: center;
            margin-bottom: 30px;
        }
        .service-issue {
            text-align: center;
            margin-bottom: 20px;
        }
        .counts {
            font-size: 18px;
            font-weight: bold;
            color: #333333;
        }
        .form-group {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Service Issue Distribution</h1>

        <form method="post" action="/">
            <div class="form-group">
                <label for="start_date">Start Date:</label>
                <input type="date" id="start_date" name="start_date">
            </div>
            <div class="form-group">
                <label for="end_date">End Date:</label>
                <input type="date" id="end_date" name="end_date">
            </div>
            <button type="submit" class="btn btn-primary">Apply Filter</button>
        </form>

        <div id="service_issue_chart" class="plotly-chart"></div>

        <div class="service-issue">
            <p class="counts">Total Issues: {{ alerts_count + request_count + self_ticket_count }}</p>
            <p class="counts">Alerts: {{ alerts_count }}</p>
            <p class="counts">Request: {{ request_count }}</p>
            <p class="counts">Self-Ticket: {{ self_ticket_count }}</p>
        </div>

        <div id="triaged_alerts_chart" class="plotly-chart"></div>
        <div id="triaged_requests_chart" class="plotly-chart"></div>
        <div id="triaged_self_tickets_chart" class="plotly-chart"></div>
    </div>

    <script>
        var serviceIssueChartJson = {{ service_issue_chart_json|safe }};
        Plotly.newPlot('service_issue_chart', serviceIssueChartJson.data, serviceIssueChartJson.layout, { responsive: true, displayModeBar: false });

        var triagedAlertsChartJson = {{ triaged_alerts_chart_json|safe }};
        Plotly.newPlot('triaged_alerts_chart', triagedAlertsChartJson.data, triagedAlertsChartJson.layout, { responsive: true, displayModeBar: false });

        var triagedRequestsChartJson = {{ triaged_requests_chart_json|safe }};
        Plotly.newPlot('triaged_requests_chart', triagedRequestsChartJson.data, triagedRequestsChartJson.layout, { responsive: true, displayModeBar: false });

        var triagedSelfTicketsChartJson = {{ triaged_self_tickets_chart_json|safe }};
        Plotly.newPlot('triaged_self_tickets_chart', triagedSelfTicketsChartJson.data, triagedSelfTicketsChartJson.layout, { responsive: true, displayModeBar: false });
    </script>
</body>
</html>


#component
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

def fetch_component_details(component):
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('io_database.db')

        # Construct SQL query to fetch top 10 details for the selected component
        query = f"SELECT Detail1, COUNT(*) AS Count FROM ServiceDesk WHERE Component = ? GROUP BY Detail1"
        query += " ORDER BY Count DESC"  # Sort by count in descending order
        query += " LIMIT 10;"  # Limit to top 10 details
        df = pd.read_sql_query(query, conn, params=(component,))

        return df
    except Exception as e:
        print(f"Error fetching component details for {component}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame if error occurs
    finally:
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    date_range_label = ""
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        # Retrieve form data (start_date and end_date)
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
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

    return render_template('index.html', graph_json=graph_json, total_components=total_components,
                           component_totals=component_totals, date_range_label=date_range_label)

@app.route('/details/<component>')
def component_details(component):
    # Fetch details for the specified component
    df = fetch_component_details(component)

    # Create JSON response with details data
    details_data = {
        "component": component,
        "details": df.to_dict('records') if not df.empty else []
    }

    return jsonify(details_data)

if __name__ == '__main__':
    app.run(debug=True)


    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Desk Component Counts</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            padding-top: 50px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            background-color: #ffffff;
            animation: fadeIn 0.5s ease-in-out; /* Apply fade-in animation */
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        h1 {
            text-align: center;
            color: #007bff;
            margin-bottom: 30px;
            animation: slideInDown 0.5s ease-in-out; /* Apply slide-in animation */
        }
        @keyframes slideInDown {
            from { transform: translateY(-50px); }
            to { transform: translateY(0); }
        }
        #plotly-chart {
            margin-bottom: 40px;
        }
        ul {
            list-style: none;
            padding-left: 0;
        }
        li {
            margin-bottom: 12px;
            font-size: 16px;
            color: #555;
            cursor: pointer; /* Change cursor to pointer for clickable items */
            transition: all 0.3s ease-in-out; /* Apply smooth transition */
        }
        li:hover {
            color: #007bff; /* Change color on hover */
        }
        .date-range-label {
            font-size: 16px;
            font-style: italic;
            color: #888;
            margin-bottom: 20px;
        }
        .modal-content {
            animation: slideInUp 0.5s ease-in-out; /* Apply slide-in animation to modal */
        }
        @keyframes slideInUp {
            from { transform: translateY(50px); }
            to { transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Service Desk Component Counts</h1>

        <form method="POST" action="/">
            <div class="form-group">
                <label for="start_date">Start Date:</label>
                <input type="date" id="start_date" name="start_date">
            </div>
            <div class="form-group">
                <label for="end_date">End Date:</label>
                <input type="date" id="end_date" name="end_date">
            </div>
            <button type="submit" class="btn btn-primary">Apply Filter</button>
        </form>

        {% if date_range_label %}
            <p class="date-range-label">{{ date_range_label }}</p>
        {% endif %}

        <div id="plotly-chart"></div>

        <p><strong>Total Components:</strong> {{ total_components }}</p>

        <h3>Component Totals</h3>
        <ul class="component-list">
            {% for component, count in component_totals.items() %}
                <li onclick="fetchComponentDetails('{{ component }}');" class="component-item"><strong>{{ component }}:</strong> {{ count }}</li>
            {% endfor %}
        </ul>
    </div>

    <!-- Modal to display component details -->
    <div class="modal fade" id="detailsModal" tabindex="-1" role="dialog" aria-labelledby="detailsModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="detailsModalLabel">Component Details</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body" id="detailsBody">
                    <!-- Component details will be displayed here -->
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        // Load the Plotly chart from JSON data
        var graphJson = {{ graph_json|safe }};
        Plotly.newPlot('plotly-chart', graphJson.data, graphJson.layout, { responsive: true });

        // Function to fetch and display component details in modal
        function fetchComponentDetails(component) {
            fetch(`/details/${component}`)
            .then(response => response.json())
            .then(data => {
                console.log(data);

                // Construct HTML for component details
                let detailsHtml = '<ul>';
                data.details.forEach(detail => {
                    detailsHtml += `<li><strong>${detail.Detail1}:</strong> ${detail.Count}</li>`;
                });
                detailsHtml += '</ul>';

                // Update modal body with component details
                document.getElementById('detailsBody').innerHTML = detailsHtml;

                // Show the modal using Bootstrap modal method
                $('#detailsModal').modal('show');
            })
            .catch(error => {
                console.error('Error fetching component details:', error);
                alert('Error fetching component details. Please try again.');
            });
        }
    </script>
</body>
</html>


#engineer
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

    return render_template('index.html', graph_json=graph_json,
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

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tickets by Engineer</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <style>
        body {
            background-color: #f8f9fa;
            color: #333;
            font-family: Arial, sans-serif;
        }
        h1, h2 {
            text-align: center;
            margin-top: 20px;
        }
        .container {
            margin-top: 40px;
        }
        .form-row {
            margin-bottom: 20px;
        }
        .table-responsive {
            margin-top: 20px;
        }
        .engineer-row {
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .engineer-row:hover {
            background-color: #e9ecef;
        }
        .modal-content {
            border-radius: 10px;
        }
        .modal-header {
            background-color: #007bff;
            color: white;
        }
        .modal-header .close {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Tickets Assigned to Engineers</h1>
        
        <!-- Date range selection form -->
        <form method="POST" action="/" class="bg-light p-4 rounded shadow-sm">
            <div class="form-row">
                <div class="col">
                    <input type="date" class="form-control" name="start_date" placeholder="Start Date">
                </div>
                <div class="col">
                    <input type="date" class="form-control" name="end_date" placeholder="End Date">
                </div>
                <div class="col">
                    <button type="submit" class="btn btn-primary btn-block">Apply Filter</button>
                </div>
            </div>
        </form>

        <!-- Display date range label -->
        {% if date_range_label %}
            <h2>{{ date_range_label }}</h2>
        {% endif %}

        <!-- Display Plotly bar chart -->
        <div id="ticketChart"></div>

        <!-- Display ticket counts by engineer in a table -->
        <h2 class="mt-4">Ticket Counts by Engineer</h2>
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead class="thead-dark">
                    <tr>
                        <th>Engineer Name</th>
                        <th>Ticket Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for engineer in engineers_data %}
                        <tr class="engineer-row" data-engineer="{{ engineer['Assignee'] }}">
                            <td>{{ engineer['Assignee'] }}</td>
                            <td>{{ engineer['TicketCount'] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal to display engineer details -->
    <div class="modal fade" id="engineerModal" tabindex="-1" role="dialog" aria-labelledby="engineerModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="engineerModalLabel">Engineer Details</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <ul id="engineerDetailsList" class="list-group"></ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        $(document).ready(function() {
            $('.engineer-row').on('click', function() {
                var engineerName = $(this).data('engineer');
                
                $.ajax({
                    type: 'POST',
                    url: '/engineer-details',
                    contentType: 'application/json;charset=UTF-8',
                    data: JSON.stringify({ engineerName: engineerName }),
                    success: function(response) {
                        var details = response.details;
                        var engineerDetailsList = $('#engineerDetailsList');
                        engineerDetailsList.empty();
                        
                        engineerDetailsList.append('<li class="list-group-item active"><strong>' + details.engineerName + '</strong></li>');
                        $.each(details.details, function(issue, count) {
                            engineerDetailsList.append('<li class="list-group-item">' + issue + ': ' + count + '</li>');
                        });
                        
                        $('#engineerModal').modal('show');
                    }
                });
            });
        });

        // Display Plotly bar chart
        var graphJson = {{ graph_json|tojson|safe }};
        var figure = JSON.parse(graphJson);
        Plotly.newPlot('ticketChart', figure.data, figure.layout);
    </script>

    <!-- Bootstrap and jQuery scripts -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>

# BU wise
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

# Function to fetch the top 10 breakdown data for a specific service issue
def fetch_breakdown_data(service_issue):
    conn = sqlite3.connect('io_database.db')
    query = """
        SELECT Component,
               Detail1,
               COUNT(*) AS Count
        FROM ServiceDesk
        WHERE ServiceIssue = ?
        GROUP BY Component, Detail1
        ORDER BY Count DESC
        LIMIT 10
    """
    df = pd.read_sql_query(query, conn, params=[service_issue])
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

    return render_template('bu_wise.html', graph_json=graph_json, 
                           triaged_business=triaged_business, 
                           date_range_label=date_range_label, 
                           total_issues=total_issues, 
                           issues_data=issues_data)

@app.route('/breakdown', methods=['POST'])
def breakdown():
    service_issue = request.form.get('service_issue')
    breakdown_data = fetch_breakdown_data(service_issue)
    breakdown_html = breakdown_data.to_html(classes='table table-striped table-bordered', index=False)
    return breakdown_html

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
                        <tr class="issue-row" data-service-issue="{{ issue['ServiceIssue'] }}">
                            <td>{{ issue['TriagedBusiness'] }}</td>
                            <td>{{ issue['ServiceIssue'] }}</td>
                            <td>{{ issue['IssueCount'] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Breakdown Modal -->
        <div class="modal fade" id="breakdownModal" tabindex="-1" role="dialog" aria-labelledby="breakdownModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="breakdownModalLabel">Breakdown Data</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body" id="breakdownContainer">
                        <!-- Breakdown data will be appended here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        $(document).ready(function() {
            // Display Plotly chart
            var graphJson = {{ graph_json|tojson|safe }};
            var figure = JSON.parse(graphJson);
            Plotly.newPlot('ticketChart', figure.data, figure.layout);

            // Handle click on service issue rows to fetch and display breakdown
            $('.issue-row').click(function() {
                var serviceIssue = $(this).data('service-issue');
                $.ajax({
                    url: '/breakdown',
                    type: 'POST',
                    data: { service_issue: serviceIssue },
                    success: function(response) {
                        $('#breakdownContainer').html(response);
                        $('#breakdownModal').modal('show'); // Show the modal
                    }
                });
            });
        });
    </script>

    <!-- Bootstrap and jQuery scripts -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>

# Utilization

import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime, timedelta

app = Flask(__name__)

# Function to fetch utilization data based on date range excluding Sundays
def fetch_utilization_data(start_date=None, end_date=None):
    conn = sqlite3.connect('io_database.db')
    
    query = """
        SELECT Assignee, SUM(TimeSpent) AS TotalTimeSpent
        FROM ServiceDesk
    """
    
    # Add date range filter to the query if provided
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date
        
        # Exclude Sundays
        dates = [start + timedelta(days=i) for i in range((end - start).days) if (start + timedelta(days=i)).weekday() != 6]
        formatted_dates = [date.strftime("%Y-%m-%d") for date in dates]
        formatted_start_date = formatted_dates[0]
        formatted_end_date = formatted_dates[-1]
        
        query += f" WHERE Created BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"
    
    query += """
        GROUP BY Assignee
        ORDER BY TotalTimeSpent DESC;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert TotalTimeSpent from seconds to hours
    df['TotalTimeSpentHours'] = df['TotalTimeSpent'] / 3600
    
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

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default date range (None if not provided)
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    # Fetch utilization data based on the selected date range
    data = fetch_utilization_data(start_date, end_date)

    # Calculate total time spent for percentage calculation
    total_time_spent = data['TotalTimeSpent'].sum()

    # Add a column for percentage utilization
    data['Percentage'] = (data['TotalTimeSpent'] / total_time_spent) * 100

    # Create a Plotly bar chart
    fig = px.bar(data, x='Assignee', y='TotalTimeSpentHours',
                 title='Engineer Utilization',
                 labels={'Assignee': 'Engineer Name', 'TotalTimeSpentHours': 'Total Utilization (hours)'},
                 text='Percentage',
                 hover_data={'Percentage': ':.2f'})

    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title='Total Time Spent (hours)')

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    # Convert data to dict for table rendering
    table_data = data.to_dict('records')

    # Prepare date range label
    date_range_label = f"Data from {start_date} to {end_date}" if start_date and end_date else "All Data"

    return render_template('index.html', graph_json=graph_json, table_data=table_data, date_range_label=date_range_label, start_date=start_date, end_date=end_date)

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

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Engineer Utilization</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <style>
        body {
            background-color: #f8f9fa;
            font-family: 'Arial', sans-serif;
            padding-top: 50px;
        }
        h1, h2 {
            text-align: center;
            color: #343a40;
        }
        #utilizationChart {
            margin-top: 30px;
        }
        .table-responsive {
            margin-top: 20px;
        }
        .table {
            animation: fadeIn 1s ease-in-out;
            background-color: #ffffff;
        }
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
            transition: background-color 0.3s ease;
        }
        .btn-primary:hover {
            background-color: #0056b3;
            border-color: #0056b3;
        }
        .engineer-row {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Engineer Utilization</h1>

        <!-- Date range selection form -->
        <form method="POST" action="/">
            <div class="form-row justify-content-center">
                <div class="col-md-4">
                    <input type="date" class="form-control" name="start_date" value="{{ start_date }}" placeholder="Start Date">
                </div>
                <div class="col-md-4">
                    <input type="date" class="form-control" name="end_date" value="{{ end_date }}" placeholder="End Date">
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-primary btn-block"><i class="fas fa-filter"></i> Apply Filter</button>
                </div>
            </div>
        </form>

        <!-- Display date range label -->
        <h2 class="text-center mt-4">{{ date_range_label }}</h2>

        <!-- Display Plotly bar chart -->
        <div id="utilizationChart" class="mt-5"></div>

        <!-- Display utilization table -->
        <div class="table-responsive mt-4">
            <table class="table table-striped table-bordered">
                <thead class="thead-dark">
                    <tr>
                        <th>Engineer Name</th>
                        <th>Total Utilization (hours)</th>
                        <th>Percentage Utilization</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                        <tr class="engineer-row" data-assignee="{{ row['Assignee'] }}" data-toggle="modal" data-target="#breakdownModal">
                            <td>{{ row['Assignee'] }}</td>
                            <td>{{ row['TotalTimeSpentHours']|round(2) }}</td>
                            <td>{{ row['Percentage']|round(2) }}%</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal for breakdown data -->
    <div class="modal fade" id="breakdownModal" tabindex="-1" role="dialog" aria-labelledby="breakdownModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="breakdownModalLabel">Breakdown Data</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body" id="breakdownContent">
                    <!-- Breakdown data will be appended here -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        $(document).ready(function() {
            // Display Plotly chart
            var graphJson = {{ graph_json|tojson|safe }};
            var figure = JSON.parse(graphJson);
            Plotly.newPlot('utilizationChart', figure.data, figure.layout);

            // Handle click event on engineer rows
            $('.engineer-row').click(function() {
                var assignee = $(this).data('assignee');
                var start_date = $('input[name="start_date"]').val();
                var end_date = $('input[name="end_date"]').val();
                fetchBreakdownData(assignee, start_date, end_date);
            });

            // Function to fetch breakdown data for a specific engineer
            function fetchBreakdownData(assignee, start_date, end_date) {
                $.ajax({
                    type: 'GET',
                    url: `/breakdown/${assignee}`,
                    data: { start_date: start_date, end_date: end_date },
                    success: function(data) {
                        // Build breakdown data as a list
                        var breakdownList = '<ul>';
                        data.forEach(function(item) {
                            breakdownList += '<li>' + item.TriagedBusiness + ': ' + item.IssueCount + '</li>';
                        });
                        breakdownList += '</ul>';

                        // Set modal title with engineer's name
                        $('#breakdownModalLabel').text('Breakdown for ' + assignee);

                        // Display breakdown list in modal body
                        $('#breakdownContent').html(breakdownList);

                        // Show the modal
                        $('#breakdownModal').modal('show');
                    },
                    error: function(xhr, status, error) {
                        console.error('Error fetching breakdown data:', error);
                    }
                });
            }
        });
    </script>

    <!-- Bootstrap and jQuery scripts -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>

# sla
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

    return render_template('index.html', graph_json=graph_json, sla_table_data=sla_table_data,
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

    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLA Distribution</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        .container {
            margin-top: 50px;
            background-color: #fff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }

        .form-row {
            margin-bottom: 20px;
        }

        .form-control {
            border-radius: 20px;
        }

        .btn-primary {
            border-radius: 20px;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background-color: #0069d9;
            border-color: #0062cc;
        }

        .table {
            margin-top: 20px;
            width: 100%;
            background-color: #fff;
        }

        .table th,
        .table td {
            padding: 15px;
            text-align: left;
            border-top: 1px solid #dee2e6;
        }

        .table th {
            background-color: #f8f9fa;
            color: #333;
            font-weight: 500;
        }

        .table-striped tbody tr:nth-of-type(odd) {
            background-color: rgba(0, 0, 0, 0.05);
        }

        /* Change cursor to pointer when hovering over table rows */
        .table tbody tr:hover {
            cursor: pointer;
        }

        .modal-content {
            border-radius: 20px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
        }

        .modal-title {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SLA Distribution</h1>
        
        <!-- Date range selection form -->
        <form method="POST" action="/">
            <div class="form-row">
                <div class="col">
                    <input type="date" class="form-control" id="start_date" name="start_date" value="{{ start_date }}" placeholder="Start Date">
                </div>
                <div class="col">
                    <input type="date" class="form-control" id="end_date" name="end_date" value="{{ end_date }}" placeholder="End Date">
                </div>
                <div class="col">
                    <button type="submit" class="btn btn-primary">Apply Filter</button>
                </div>
            </div>
        </form>

        <!-- Display selected date range -->
        {% if start_date and end_date %}
            <div class="alert alert-info" role="alert">Data from <strong>{{ start_date }}</strong> to <strong>{{ end_date }}</strong></div>
        {% endif %}

        <!-- Display Plotly donut pie chart -->
        <div id="slaChart"></div>

        <!-- Display SLA data table -->
        <div class="table-responsive">
            <table class="table table-striped" id="slaTable">
                <thead>
                    <tr>
                        <th>SLA</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in sla_table_data %}
                        <tr data-sla="{{ row['SLA'] }}">
                            <td>{{ row['SLA'] }}</td>
                            <td>{{ row['Count'] }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Modal for breakdown data -->
        <div class="modal fade" id="breakdownModal" tabindex="-1" role="dialog" aria-labelledby="breakdownModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="breakdownModalLabel">Breakdown Data</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body" id="breakdownModalBody">
                        <!-- Breakdown data will be inserted here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>
        // Display Plotly donut pie chart
        var graphJson = {{ graph_json|tojson|safe }};
        var figure = JSON.parse(graphJson);
        Plotly.newPlot('slaChart', figure.data, figure.layout);

        // Handle click on SLA table rows
        $('#slaTable').on('click', 'tr', function() {
            var sla = $(this).data('sla');
            fetchBreakdownData(sla);
        });

        // Function to fetch breakdown data
        function fetchBreakdownData(sla) {
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            fetch('/breakdown', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sla: sla, start_date: start_date, end_date: end_date })
            })
            .then(response => response.text())
            .then(data => {
                // Display breakdown data in the modal body
                $('#breakdownModalBody').html(data);
                // Show the modal
                $('#breakdownModal').modal('show');
            })
            .catch(error => console.error('Error fetching breakdown data:', error));
        }
    </script>
</body>
</html>
