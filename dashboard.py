from flask import Flask, render_template, request , jsonify
import json
import plotly
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
    graph_json = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        # data = utilization.get_data(start_date, end_date)
    # 
    return utilization.get_data(start_date, end_date)

app.route('/utilization_breakdown', methods=['POST'])
def utilization_breakdown():
    utilization_data = request.json['utilization']
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    print(start_date, end_date, utilization_data)
    return sla.get_breakdown(utilization_data, start_date, end_date)
@app.route('/breakdown/<assignee>')
def breakdown(assignee):
    # Get date range from request args
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Fetch breakdown data for the selected engineer
    breakdown_data = utilization.fetch_breakdown_data(assignee, start_date, end_date)

    # Convert breakdown data to a dictionary for JSON response
    breakdown_dict = breakdown_data.to_dict('records')

    return jsonify(breakdown_dict)

@app.route('/sla', methods=['GET', 'POST'])
def sla_page():
    sla_data = None
    graph_json = None
    start_date= None
    end_date = None
    breakdown_sla = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        breakdown_sla = request.form.get('breakdown_sla')
    elif request.method == 'GET':
        # Handle GET request (if needed)
        pass
    sla_data = sla.fetch_sla_data(start_date, end_date)
    
    if sla_data is not None and not sla_data.empty:
       return sla.set_graph_data(breakdown_sla, start_date, end_date)
    # graph_json = json.dumps(sla.get_graph(sla_data), cls=plotly.utils.PlotlyJSONEncoder)
    # return render_template('sla.html', sla_table_data=sla_data.to_dict('records') if sla_data is not None else None, graph_json=graph_json)

@app.route('/sla_breakdown', methods=['POST'])
def sla_breakdown():
    sla_data = request.json['sla']
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    print(start_date, end_date, sla_data)
    return sla.get_breakdown(sla_data, start_date, end_date)

@app.route('/service_issue_distribution', methods=['GET', 'POST'])
def service_issue_distribution_page():
    # data = None
    # start_date = None
    # end_date = None
    # graph_json = None
    # if request.method == 'POST':
    #     triaged_business = request.form.get('triaged_business')
    #     start_date = request.form.get('start_date')
    #     end_date = request.form.get('end_date')
        # data = service_issue_distribution.get_data(triaged_business, start_date, end_date)
        # if data is not None and not data.empty:
        #     graph_json = json.dumps(service_issue_distribution.get_graph(data), cls=plotly.utils.PlotlyJSONEncoder)
    # return render_template('service_issue_distribution.html', data=data.to_dict('records') if data is not None else None, graph_json=graph_json)
    return service_issue_distribution.get_data()

@app.route('/engineer', methods=['GET', 'POST'])
def engineer_page():
    # data = None
    # start_date = None
    # end_date = None
    # if request.method == 'POST':
    #     start_date = request.form.get('start_date')
    #     end_date = request.form.get('end_date')
        
    # return render_template('engineer.html', data=data)
    return engineer.get_data()

@app.route('/engineer-details', methods=['POST'])
def engineer_details(start_date, end_date):
    data = request.get_json()
    engineer_name = data['engineerName']
    
    # Fetch engineer details
    details_df = engineer.fetch_engineer_details(engineer_name)
    details_dict = details_df.set_index('ServiceIssue')['IssueCount'].to_dict()
    
    return jsonify(details={'engineerName': engineer_name, 'details': details_dict} )

@app.route('/component', methods=['GET', 'POST'])
def component_page():
    # data = None
    # start_date = None
    # end_date = None
    # if request.method == 'POST':
    #     start_date = request.form.get('start_date')
    #     end_date = request.form.get('end_date')
    return component.get_data()
    # return render_template('component.html', data=data)

@app.route('/comp_details', methods=['POST'])
def component_details():
    # Fetch details for the specified component
    start_date = request.json['start_date']
    end_date = request.json['end_date']
    comp = request.json['comp']
    df = component.fetch_component_details(comp, start_date, end_date)

    # Create JSON response with details data
    details_data = {
        "component": comp,
        "details": df.to_dict('records') if not df.empty else []
    }

    return jsonify(details_data)

@app.route('/bu_wise', methods=['GET', 'POST'])
def bu_wise_page():
    data = None
    start_date = None
    end_date = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    return bu_wise.get_data(start_date, end_date)
    # return render_template('bu_wise.html', data=data)


@app.route('/bu_breakdown', methods=['POST'])
def bu_breakdown():
    service_issue = request.form.get('service_issue')
    breakdown_data = bu_wise.fetch_breakdown_data(service_issue)
    breakdown_html = breakdown_data.to_html(classes='table table-striped table-bordered', index=False)
    return breakdown_html

if __name__ == '__main__':
    app.run(debug=True)
