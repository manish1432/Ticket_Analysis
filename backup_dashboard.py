\from flask import Flask, render_template, request , jsonify
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
def engineer_details():
    data = request.get_json()
    engineer_name = data['engineerName']
    
    # Fetch engineer details
    details_df = engineer.fetch_engineer_details(engineer_name)
    details_dict = details_df.set_index('ServiceIssue')['IssueCount'].to_dict()
    
    return jsonify(details={'engineerName': engineer_name, 'details': details_dict})

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

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
</head>
<body>
    <div class="container">
        <h1 class="text-center">Technicolor Group IO Dashboard</h1>
        <ul class="nav nav-tabs" id="dashboardTabs" role="tablist">
            <li class="nav-item">
                <a class="nav-link active" id="bu-wise-tab" data-toggle="tab" href="#bu-wise" role="tab" aria-controls="bu-wise" aria-selected="true">BU Wise</a>
            </li>
            <li class="nav-item">
            
                <a class="nav-link" id="sla-tab" data-toggle="tab" href="#sla" role="tab" aria-controls="sla" aria-selected="false">SLA</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="utilization-tab" data-toggle="tab" href="#utilization" role="tab" aria-controls="utilization" aria-selected="false">Utilization</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="service-issue-tab" data-toggle="tab" href="#service-issue" role="tab" aria-controls="service-issue" aria-selected="false">Service Issue Distribution</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="engineer-tab" data-toggle="tab" href="#engineer" role="tab" aria-controls="engineer" aria-selected="false">Engineer</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="component-tab" data-toggle="tab" href="#component" role="tab" aria-controls="component" aria-selected="false">Component</a>
            </li>
            
        </ul>
        <div class="tab-content" id="dashboardTabsContent">
            <div class="tab-pane fade" id="sla" role="tabpanel" aria-labelledby="sla-tab">
                
            </div>
            <div class="tab-pane fade" id="utilization" role="tabpanel" aria-labelledby="utilization-tab">
                
            </div>
            <div class="tab-pane fade" id="service-issue" role="tabpanel" aria-labelledby="service-issue-tab">
                
            </div>
            <div class="tab-pane fade" id="engineer" role="tabpanel" aria-labelledby="engineer-tab">
                
            </div>
            <div class="tab-pane fade" id="component" role="tabpanel" aria-labelledby="component-tab">
                
            </div>
            <div class="tab-pane fade show active" id="bu-wise" role="tabpanel" aria-labelledby="bu-wise-tab">
                
            </div>
        </div>
    </div>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>
        $(document).ready(function()
        {
            get_bu_wise()
            $('#engineer-tab').click(function(){ get_engineer();});
            $('#sla-tab').click(function(){ get_sla();});
            $('#component-tab').click(function(){ get_component();});
            $('#utilization-tab').click(function(){ get_utilization();});
            $('#service-issue-tab').click(function(){ get_service_issue_distribution();});
        }
    );
        function get_bu_wise()
        {
            $.ajax({
                    url: '/bu_wise',
                    type: 'GET',
                    // data: { service_issue: serviceIssue },
                    success: function(response) {
                        $('#bu-wise').html(response);
                        // $('#breakdownModal').modal('show'); // Show the modal
                    }
                });

        }function get_engineer() {
            $.ajax({
                url: '/engineer',
                type: 'GET',
                success: function(data) {
                    $('#engineer').html(data);
                },
                error: function(error) {
                    console.error('Error fetching Engineer data:', error);
                }
            });
        }

        function get_sla() {
            $.ajax({
                url: '/sla',
                type: 'GET',
                success: function(data) {
                    $('#sla').html(data);
                },
                error: function(error) {
                    console.error('Error fetching Sla data:', error);
                }
            });
        }
   
        function get_component() {
            $.ajax({
                url: '/component',
                type: 'GET',
                success: function(data) {
                    $('#component').html(data);
                },
                error: function(error) {
                    console.error('Error fetching Component data:', error);
                }
            });
        }

        function get_utilization() {
            $.ajax({
                url: '/utilization',
                type: 'GET',
                success: function(data) {
                    // console.log(data)
                    $('#utilization').html(data);
                },
                error: function(error) {
                    console.error('Error fetching Utilization data:', error);
                }
            });
        }

        function get_service_issue_distribution() {
            $.ajax({
                url: '/service_issue_distribution',
                type: 'GET',
                success: function(data) {
                    // console.log(data)
                    $('#service-issue').html(data);
                },
                error: function(error) {
                    console.error('Error fetching servive_issue_distribution data:', error);
                }
            });
        }
        
    
    </script>
</body>
</html>