import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import *
from plotly.graph_objs.scatter.marker import Line
import numpy as np

import plot_settings

USERNAME_PASSWORD_PAIRS = [
    ['evan.mcgoff', 'meow']
]

app = dash.Dash()
auth = dash_auth.BasicAuth(app,USERNAME_PASSWORD_PAIRS)
server = app.server

# function to get file from google drive
def pull_google_drive(url):
    file_id = url.split('/')[-2]
    dwn_url = "https://drive.google.com/uc?id=" + file_id
    tmp = pd.read_excel(dwn_url)

    return tmp

# filter to columns needed and format names
def reformat_df(d):
    tmp = d.filter(['Date', 'Spread', 'SPX_Price'])
    tmp.columns = [x.lower() for x in tmp.columns]
    tmp = tmp.assign(date=lambda t: pd.to_datetime(t.date),
                   inverse=lambda t: 1 / (t.spread / 100))
    tmp = tmp.sort_values(by='date').reset_index(drop=True)

    return tmp

# do date filter and recalculate stds
def calc_stds(d, start_date, end_date):
    df_period = d.query(f"date>=@start_date & date<=@end_date").reset_index(drop=True)
    mean = df_period.spread.mean()
    std = df_period.spread.std()
    std_1up = mean + std
    std_1down = mean - std
    std_2up = mean + 2*std
    std_2down = mean - 2*std

    return df_period, mean, std_1up, std_1down, std_2up, std_2down

def create_graph(plot_df, mean, up1, down1, up2, down2):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=plot_df['date'],
                             y=plot_df['spread']))

    fig.update_traces(marker=dict(size=3))

    hline_color = "black"  # "#848484"

    fig.add_hline(y=mean,
                  line_width=2,
                  line_color=hline_color,
                  annotation_text=f"{mean:,.2f} (mean)",
                  annotation_position="bottom right"
                  )

    fig.add_hline(y=up1,
                  line_dash="dash",
                  line_width=1,
                  line_color=hline_color,
                  annotation_text=f"{up1:,.2f}",
                  annotation_position="bottom right"
                  )

    fig.add_hline(y=up2,
                  line_dash="dot",  # "dash"
                  line_width=1,
                  line_color=hline_color,
                  annotation_text=f"{up2:,.2f}",
                  annotation_position="bottom right"
                  )

    fig.add_hline(y=down1,
                  line_dash="dash",
                  line_width=1,
                  line_color=hline_color,
                  annotation_text=f"{down1:,.2f}",
                  annotation_position="bottom right"
                  )

    fig.add_hline(y=down2,
                  line_dash="dot",  # "dash"
                  line_width=1,
                  line_color=hline_color,
                  annotation_text=f"{down2:,.2f}",
                  annotation_position="bottom right"
                  )

    fig.update_xaxes(showgrid=False,
                     range=[plot_df.date.min(), plot_df.date.max()])

    fig.update_yaxes(showgrid=False,
                     zeroline=False,
                     title='Equity Risk Premium',
                     ticksuffix="  ",
                     range=[-.5, np.ceil(plot_df.spread.max())])

    fig.update_layout(font_family="Avenir",
                      font_color="#4c4c4c",
                      font_size=14,
                      showlegend=False,
                      title=dict(font_size=22,
                                 text="<b>Equity risk premium mainly between 15yr mean and -1 std in recent months</b>",
                                 ),
                      title_x=0.04,
                      title_y=0.95,
                      #                   title_pad_b=1000
                      )

    # annotations
    annotations = []

    points = [up2, up1, mean, down1, down2]
    labels = ["+2\u03C3", "+1\u03C3", "mean", "-1\u03C3", "-2\u03C3"]

    for p, l in zip(points, labels):
        annotations.append(dict(xref='paper',
                                x=1.005,
                                y=p,
                                xanchor='left',
                                yanchor='middle',
                                align='left',
                                text=f"{p:.2f} ({l})",
                                showarrow=False,
                                font=dict(size=12, color=hline_color)
                                ))

    fig.update_layout(annotations=annotations, template=plot_settings.dockstreet_template)

    fig.add_annotation(x=0.03,
                       y=mean + .2,
                       xref='paper',
                       yref='y',
                       xanchor='left',
                       align='left',
                       borderpad=5,
                       text="Cheaper",
                       axref='pixel',
                       ayref='y',
                       ax=0.25,
                       ay=mean + 3.8,
                       arrowhead=1,
                       arrowsize=1.,
                       arrowside='start',
                       arrowwidth=1.5,
                       arrowcolor="#767676",
                       showarrow=True,
                       font=dict(size=15,
                                 color="#767676"
                                 ))

    fig.add_annotation(x=0.03,
                       y=mean - .2,
                       xref='paper',
                       yref='y',
                       xanchor='left',
                       align='left',
                       borderpad=5,
                       text="More Expensive",
                       axref='pixel',
                       ayref='y',
                       ax=0.25,
                       ay=mean - 3.8,
                       arrowhead=1,
                       arrowsize=1.,
                       arrowside='start',
                       arrowwidth=1.5,
                       arrowcolor="#767676",
                       showarrow=True,
                       font=dict(size=15,
                                 color="#767676"
                                 ))

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(count=2,
                         label="2y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True,
                range=[plot_df.date.min(), plot_df.date.max()]
            ),
            type="date"
        )
    )

    for ser in fig['data']:
        ser['hovertemplate'] = "%{x|%b %-d, %Y}, %{y:.2f}<extra></extra>"

    return fig

# load the data from google drive
url = "https://drive.google.com/file/d/16NBIP4qGtBkNbcxfUElMDjWiADryMa-G/view?usp=sharing"
df = pull_google_drive(url)

# format columns
df = reformat_df(df)

df_date_filter, m, u1, d1, u2, d2 = calc_stds(df, datetime(2007,1,1), datetime.today())

updated_figure = create_graph(df_date_filter, m, u1, d1, u2, d2)

# app layout
app.layout = html.Div([
    html.H1('Earnings Spread'),

    html.Div([
        html.H3('Enter a start and end date:', style={'paddingRight':'30px'}),
        dcc.DatePickerRange(id='my_date_range',
                            min_date_allowed=df.date.min(),
                            max_date_allowed=df.date.max(),
                            start_date=datetime(2007,1,1),
                            end_date=datetime.today()
                            )
    ], style={'display':'inline-block'}),

    html.Div([
        html.Button(id='submit_button',
                    n_clicks=0,
                    children='Submit',
                    style={'fontSize':24, 'marginLeft':'30px'})
    ], style={'display':'inline-block'}),

    dcc.Graph(id='my_graph',
              figure=updated_figure)
])

@app.callback(Output('my_graph','figure'),
              [Input('submit_button','n_clicks')],
              [
                  State('my_date_range','start_date'),
                  State('my_date_range','end_date')
              ])
def callback_dates(n_clicks, start_date, end_date):
    # when it gets passed into the input, converts it to a string
    start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end = datetime.strptime(end_date[:10], '%Y-%m-%d')

    df_date_filter, m, u1, d1, u2, d2 = calc_stds(df, start, end)

    updated_figure = create_graph(df_date_filter, m, u1, d1, u2, d2)

    return updated_figure

if __name__ == '__main__':
    app.run_server()
