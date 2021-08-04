import plotly.graph_objs as go

background_color = "#ffffff"
grid_color = "#f2f0f0"
color_list = ['#5C943D', "#bababa"]

dockstreet_template = go.layout.Template(
    layout=go.Layout(
        colorway=color_list,
        font={"color": "black", "family": "sans-serif"},
        mapbox={"style": "light"},
        paper_bgcolor=background_color,
        plot_bgcolor=background_color,
        hovermode="closest",
        xaxis={
            "automargin": True,
            "gridcolor": grid_color,
            "linecolor": grid_color,
            "ticks": "",
            "zerolinecolor": grid_color,
            "zerolinewidth": 2,
        },
        yaxis={
            "automargin": True,
            "gridcolor": grid_color,
            "linecolor": grid_color,
            "ticks": "",
            "zerolinecolor": grid_color,
            "zerolinewidth": 2,
            "title_standoff": 10,
        },
    )
)