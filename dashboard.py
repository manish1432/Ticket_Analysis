from flask import Flask, render_template, request, jsonify
import json
import plotly
import pandas as pd
import utilization
import sla
import service_issue_distribution
import engineer
import component
import bu_wise
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/utilization', methods=['GET', 'POST'])
def utilization_page():
    data = None
    start_date = None
    end_date = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    return utilization.get_data(start_date, end_date)

@app.route('/utilization_breakdown', methods=['POST'])
def utilization_breakdown():
    utilization_data = request.json['utilization']
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    return sla.get_breakdown(utilization_data, start_date, end_date)

@app.route('/breakdown/<assignee>')
def breakdown(assignee):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    breakdown_data = utilization.fetch_breakdown_data(assignee, start_date, end_date)
    breakdown_dict = breakdown_data.to_dict('records')
    return jsonify(breakdown_dict)

@app.route('/sla', methods=['GET', 'POST'])
def sla_page():
    sla_data = None
    start_date = None
    end_date = None
    breakdown_sla = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        breakdown_sla = request.form.get('breakdown_sla')
    sla_data = sla.fetch_sla_data(start_date, end_date)
    if sla_data is not None and not sla_data.empty:
        return sla.set_graph_data(breakdown_sla, start_date, end_date)

@app.route('/sla_breakdown', methods=['POST'])
def sla_breakdown():
    sla_data = request.json['sla']
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    return sla.get_breakdown(sla_data, start_date, end_date)

@app.route('/service_issue_distribution', methods=['GET', 'POST'])
def service_issue_distribution_page():
    return service_issue_distribution.get_data()

@app.route('/engineer', methods=['GET', 'POST'])
def engineer_page():
    return engineer.get_data()

@app.route('/engineer-details', methods=['POST'])
def engineer_details():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    engineer_name = data['engineerName']
    
    # Parse the start and end dates if they are provided
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Fetch engineer details with the filtered date range
    details_df = engineer.fetch_engineer_details(engineer_name, start_date, end_date)
    details_dict = details_df.set_index('ServiceIssue')['IssueCount'].to_dict()
    
    return jsonify(details={'engineerName': engineer_name, 'details': details_dict})

@app.route('/component', methods=['GET', 'POST'])
def component_page():
    return component.get_data()

@app.route('/comp_details', methods=['POST'])
def get_component_details():
    data = request.json
    component_name = data.get('comp')  # Renamed variable to avoid naming conflict
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    triaged_business = data.get('triaged_business')

    # Use the correct function name from the imported module
    details_df = component.fetch_component_details(component_name, start_date, end_date, triaged_business)
    details = details_df.to_dict(orient='records')

    response = {
        'details': details,
        'triaged_business': triaged_business
    }

    return jsonify(response)


    return jsonify(response)

@app.route('/bu_wise', methods=['GET', 'POST'])
def bu_wise_page():
    data = None
    start_date = None
    end_date = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    return bu_wise.get_data(start_date, end_date)

@app.route('/bu_breakdown', methods=['POST'])
def bu_breakdown():
    service_issue = request.form.get('service_issue')
    print(service_issue)
    breakdown_data = bu_wise.fetch_breakdown_data(service_issue)
    breakdown_html = breakdown_data.to_html(classes='table table-striped table-bordered', index=False)
    print(breakdown_html)
    return breakdown_html

if __name__ == '__main__':
    app.run(debug=True)
