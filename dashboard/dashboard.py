import json
import os
from datetime import datetime

import dash
import plotly.graph_objs as go
import redis
from dash import dcc, html
from dash.dependencies import Input, Output

REDIS_HOST = os.environ.get("REDIS_HOST", "10.244.0.1")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_OUTPUT_KEY = os.environ.get("REDIS_OUTPUT_KEY", "lw337-proj3-output")

redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

app = dash.Dash(__name__)

percentage_outgoing_bytes_history = {"x": [], "y": []}
percentage_memory_caching_history = {"x": [], "y": []}
moving_avg_cpus_history = {}

app.layout = html.Div(
    [
        html.H1("Dashboard"),
        html.Div(
            [
                dcc.Graph(
                    id="percentage_outgoing_bytes-graph",
                ),
                dcc.Graph(
                    id="percentage_memory_caching-graph",
                ),
                dcc.Graph(
                    id="moving_avg_cpus_history-graph",
                ),
            ]
        ),
        dcc.Interval(id="interval-component", interval=5000),
    ]
)


@app.callback(
    [
        Output("percentage_outgoing_bytes-graph", "figure"),
        Output("percentage_memory_caching-graph", "figure"),
        Output("moving_avg_cpus_history-graph", "figure"),
    ],
    [Input("interval-component", "n_intervals")],
)
def update_metrics(_):
    global moving_avg_cpus_history, percentage_outgoing_bytes_history, percentage_memory_caching_history

    data = redis_db.get(REDIS_OUTPUT_KEY)
    metrics = json.loads(data)

    for cpu in metrics:
        if "cpu" in cpu:
            moving_avg_cpus_history[cpu] = moving_avg_cpus_history.get(
                cpu, {"x": [], "y": []}
            )
            moving_avg_cpus_history[cpu]["x"].append(datetime.now())
            moving_avg_cpus_history[cpu]["y"].append(metrics[cpu])
            moving_avg_cpus_history[cpu]["x"] = moving_avg_cpus_history[cpu]["x"][-20:]
            moving_avg_cpus_history[cpu]["y"] = moving_avg_cpus_history[cpu]["y"][-20:]

    percentage_outgoing_bytes_history["x"].append(datetime.now())
    percentage_outgoing_bytes_history["y"].append(metrics["percentage_outgoing_bytes"])
    percentage_outgoing_bytes_history["x"] = percentage_outgoing_bytes_history["x"][
        -20:
    ]
    percentage_outgoing_bytes_history["y"] = percentage_outgoing_bytes_history["y"][
        -20:
    ]

    percentage_memory_caching_history["x"].append(datetime.now())
    percentage_memory_caching_history["y"].append(metrics["percentage_memory_caching"])
    percentage_memory_caching_history["x"] = percentage_memory_caching_history["x"][
        -20:
    ]
    percentage_memory_caching_history["y"] = percentage_memory_caching_history["y"][
        -20:
    ]

    cpu_graph_data = [
        go.Scatter(
            x=moving_avg_cpus_history[cpu_key]["x"],
            y=moving_avg_cpus_history[cpu_key]["y"],
            mode="lines",
            name=cpu_key,
        )
        for cpu_key in moving_avg_cpus_history
    ]
    network_egress_graph_data = go.Scatter(
        x=percentage_outgoing_bytes_history["x"],
        y=percentage_outgoing_bytes_history["y"],
        mode="lines",
        name="Percent Network Egress",
    )
    memory_cache_graph_data = go.Scatter(
        x=percentage_memory_caching_history["x"],
        y=percentage_memory_caching_history["y"],
        mode="lines",
        name="Percent Memory Cache",
    )

    return [
        {
            "data": [network_egress_graph_data],
            "layout": {"title": "Percentage Outgoing Bytes"},
        },
        {
            "data": [memory_cache_graph_data],
            "layout": {"title": "Percentage Memory Caching"},
        },
        {"data": cpu_graph_data, "layout": {"title": "Moving Average CPU percent"}},
    ]


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8005, use_reloader=False)
