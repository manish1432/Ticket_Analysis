from flask import Flask, render_template, request
import json
import plotly
import utilization
import sla
import service_issue_distribution
import engineer
import component
import bu_wise

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/utilization', methods=['GET', 'POST'])
def utilization_page():
    data = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        data = utilization.get_data(start_date, end_date)
    return render_template('utilization.html', data=data)

@app.route('/sla', methods=['GET', 'POST'])
def sla_page():
    sla_data = None
    graph_json = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        sla_data = sla.get_data(start_date, end_date)
        if sla_data is not None and not sla_data.empty:
            graph_json = json.dumps(sla.get_graph(sla_data), cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('sla.html', sla_table_data=sla_data.to_dict('records') if sla_data is not None else None, graph_json=graph_json)

@app.route('/service_issue_distribution', methods=['GET', 'POST'])
def service_issue_distribution_page():
    data = None
    graph_json = None
    if request.method == 'POST':
        triaged_business = request.form.get('triaged_business')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        data = service_issue_distribution.get_data(triaged_business, start_date, end_date)
        if data is not None and not data.empty:
            graph_json = json.dumps(service_issue_distribution.get_graph(data), cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('service_issue_distribution.html', data=data.to_dict('records') if data is not None else None, graph_json=graph_json)

@app.route('/engineer', methods=['GET', 'POST'])
def engineer_page():
    data = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        data = engineer.get_data(start_date, end_date)
    return render_template('engineer.html', data=data)

@app.route('/component', methods=['GET', 'POST'])
def component_page():
    data = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        data = component.get_data(start_date, end_date)
    return render_template('component.html', data=data)

@app.route('/bu_wise', methods=['GET', 'POST'])
def bu_wise_page():
    data = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        data = bu_wise.get_data(start_date, end_date)
    return render_template('bu_wise.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
