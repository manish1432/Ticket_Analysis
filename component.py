import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
import plotly.express as px
from datetime import datetime

app = Flask(__name__)

def fetch_data(start_date=None, end_date=None, triaged_business=None):
    conn = sqlite3.connect('io_database.db')
    query = "SELECT Component, COUNT(*) AS Count FROM ServiceDesk"
    conditions = []
    params = []

    if start_date and end_date:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        conditions.append("Created BETWEEN ? AND ?")
        params.extend([start_date_str, end_date_str])

    if triaged_business and triaged_business != "All":
        conditions.append("TriagedBusiness = ?")
        params.append(triaged_business)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY Component ORDER BY Count DESC;"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.sort_values(by='Count', ascending=False)
    return df

def fetch_component_details(component, start_date, end_date, triaged_business=None):
    try:
        conn = sqlite3.connect('io_database.db')
        query = f"SELECT Detail1, COUNT(*) AS Count FROM ServiceDesk WHERE Component = ?"
        params = [component]

        if start_date and end_date:
            query += " AND Created >= ? AND Created <= ?"
            params.extend([start_date, end_date])

        if triaged_business and triaged_business != "All":
            query += " AND TriagedBusiness = ?"
            params.append(triaged_business)

        query += " GROUP BY Detail1 ORDER BY Count DESC LIMIT 10;"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        print(f"Error fetching component details for {component}: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def fetch_top_10_components_by_business(start_date=None, end_date=None, triaged_business=None):
    conn = sqlite3.connect('io_database.db')
    query = "SELECT Component, COUNT(*) AS Count FROM ServiceDesk"
    conditions = []
    params = []

    if start_date and end_date:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        conditions.append("Created BETWEEN ? AND ?")
        params.extend([start_date_str, end_date_str])

    if triaged_business and triaged_business != "All":
        conditions.append("TriagedBusiness = ?")
        params.append(triaged_business)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY Component, TriagedBusiness ORDER BY Count DESC LIMIT 10;"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# @app.route('/component', methods=['GET', 'POST'])
def get_data():
    date_range_label = ""
    start_date = None
    end_date = None
    triaged_business = None

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        triaged_business = request.form.get('triaged_business')

        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            date_range_label = f"Data from {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
        print(start_date, end_date)

    df = fetch_data(start_date, end_date, triaged_business)
    total_components = df['Count'].sum()

    fig = px.bar(df, x='Count', y='Component', orientation='h', title='Service Desk Component Counts',
                 labels={'Count': 'Number of Incidents', 'Component': 'Service Components'},
                 color='Count', color_continuous_scale='Blues')

    fig.update_layout(
        plot_bgcolor='#f0f0f0',
        paper_bgcolor='#f0f0f0',
        font_family='Arial',
        font_color='#333',
        title_font_size=24,
        xaxis_title_font_size=16,
        yaxis_title_font_size=16,
        legend_title_font_size=14,
        margin=dict(l=120, r=20, t=80, b=50),
        coloraxis_colorbar=dict(
            title='Incident Count',
            tickfont=dict(size=12),
            title_font_size=14,
            len=0.7,
            thickness=15
        )
    )

    graph_json = fig.to_json()
    component_totals = df.set_index('Component').to_dict()['Count']
    df_top_10 = fetch_top_10_components_by_business(start_date, end_date, triaged_business)

    pie_fig = px.pie(df_top_10, values='Count', names='Component', title='Top 10 Components by TriagedBusiness',
                     labels={'Count': 'Number of Incidents', 'Component': 'Service Components'})

    pie_fig.update_layout(
        plot_bgcolor='#f0f0f0',
        paper_bgcolor='#f0f0f0',
        font_family='Arial',
        font_color='#333',
        title_font_size=24,
        legend_title_font_size=14
    )

    pie_graph_json = pie_fig.to_json()

    return render_template('component.html', graph_json=graph_json, total_components=total_components,
                           component_totals=component_totals, date_range_label=date_range_label,
                           start_date=start_date, end_date=end_date, pie_graph_json=pie_graph_json,
                           triaged_business=triaged_business)

# @app.route('/comp_details', methods=['POST'])
# def get_component_details():
#     data = request.json
#     component = data.get('comp')
#     start_date = data.get('start_date')
#     end_date = data.get('end_date')
#     triaged_business = data.get('triaged_business')

#     details_df = fetch_component_details(component, start_date, end_date, triaged_business)
#     details = details_df.to_dict(orient='records')

#     response = {
#         'details': details,
#         'triaged_business': triaged_business
#     }

#     return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
