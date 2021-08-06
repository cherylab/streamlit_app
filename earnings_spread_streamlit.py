import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import *
from plotly.graph_objs.scatter.marker import Line
from plotly.subplots import make_subplots
import numpy as np
import plot_settings
import logins
from multiapp import MultiApp

st.set_page_config(layout='wide')

# function to get file from google drive
@st.cache
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

def create_std_graph(plot_df, mean, up1, down1, up2, down2, show_lines):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=plot_df['date'],
                             y=plot_df['spread']))

    fig.update_traces(marker=dict(size=3))

    if show_lines:

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

        fig.update_layout(annotations=annotations)

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
                           ay=plot_df.spread.max(),
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
                           ay=np.floor(plot_df.spread.min()) - .8,
                           arrowhead=1,
                           arrowsize=1.,
                           arrowside='start',
                           arrowwidth=1.5,
                           arrowcolor="#767676",
                           showarrow=True,
                           font=dict(size=15,
                                     color="#767676"
                                     ))

    fig.update_xaxes(showgrid=False if show_lines else True, # don't show axes if show mean/stds
                     range=[plot_df.date.min(), plot_df.date.max()])

    fig.update_yaxes(showgrid=False if show_lines else True, # don't show axes if show mean/stds
                     zeroline=False,
                     title='Equity Risk Premium',
                     ticksuffix="  ",
                     range=[np.floor(plot_df.spread.min())-1.5,
                            np.ceil(plot_df.spread.max())])

    fig.update_layout(font_family="Avenir",
                      font_color="#4c4c4c",
                      font_size=14,
                      showlegend=False,
                      title=dict(font_size=22,
                                 text="<b>Equity risk premium mainly between 15yr mean and -1\u03C3 lately</b>",
                                 ),
                      title_x=0.04,
                      title_y=0.95,
                      plot_bgcolor='white'
                      #                   title_pad_b=1000
                      )

    fig.update_layout(
        template=plot_settings.dockstreet_template,
        height=500,
        margin=dict(b=0),
        xaxis=dict(
            rangeselector=dict(
                y=1.05,
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

def create_inverse_graph(df_all):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=df_all.date, y=df_all.inverse,
                   name="Bond Adj. P/E Ratio"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df_all.date,
                   y=df_all.spx_price,
                   name="S&P 500 Price",
                   line=dict(width=1.5)),
        secondary_y=True,
    )

    fig.update_layout(template=plot_settings.dockstreet_template,
                      plot_bgcolor='white',
                      hovermode='x',
                      font_family="Avenir",
                      font_color="#4c4c4c",
                      title=dict(font_size=22,
                                 text="<b>S&P price and Interest Rate Adjusted P/E ratio</b>",
                                 x=0.04,
                                 y=0.93
                                 ),
                      legend=dict(
                          orientation="h",
                          yanchor="bottom",
                          y=1,
                          xanchor="right",
                          x=.37,
                          font=dict(size=14)
                      ))

    fig.update_yaxes(title_text="<b>S&P Price</b>",
                     color="#767676",
                     tickcolor="#767676",
                     tickfont_color="#767676",
                     tickfont_size=13,
                     showgrid=False,
                     tickformat="$,",
                     tickprefix="  ",
                     title_standoff=20,
                     secondary_y=True)

    fig.update_yaxes(title_text="<b>Bond Adjusted P/E</b>",
                     color=plot_settings.color_list[0],
                     tickcolor=plot_settings.color_list[0],
                     tickfont_color=plot_settings.color_list[0],
                     tickfont_size=13,
                     ticksuffix="   ",
                     range=[df_all.inverse.min() - (df_all.inverse.min() % 10) - 2,
                            df_all.inverse.max() + (df_all.inverse.max() % 10)],
                     secondary_y=False)

    fig.update_xaxes(showgrid=False)

    fig.add_annotation(x=df_all.date.max(),
                       y=df_all.spx_price.values[-1],
                       xref='x',
                       yref='y2',
                       xanchor='left',
                       align='left',
                       borderpad=5,
                       text=f"${df_all.spx_price.values[-1]:,.0f}",
                       showarrow=False,
                       font=dict(size=12,
                                 color="#767676")
                       )

    fig.add_annotation(x=df_all.date.max(),
                       y=df_all.inverse.values[-1],
                       xref='x',
                       yref='y',
                       xanchor='left',
                       align='left',
                       borderpad=5,
                       text=f"{df_all.inverse.values[-1]:,.0f}",
                       showarrow=False,
                       font=dict(size=12,
                                 color=plot_settings.color_list[0])
                       )

    for ser in fig['data']:
        if ser['name'] == "Bond Adj. P/E Ratio":
            ser['hovertemplate'] = "%{x|%b %-d, %Y}, %{y:,.2f}<extra></extra>"
        else:
            ser['hovertemplate'] = "%{x|%b %-d, %Y}, %{y:$,.2f}<extra></extra>"

    return fig

# ---------------------------------------------------------------------
# load the data from google drive
url = "https://drive.google.com/file/d/16NBIP4qGtBkNbcxfUElMDjWiADryMa-G/view?usp=sharing"
df = pull_google_drive(url)

# format columns
df = reformat_df(df)
print('max date', df.date.max())

# FIRST PAGE
def earnings_recalc():
    st.title('Earnings Spread Analysis')

    # st.sidebar.write('<br><b>Date Inputs</b>', unsafe_allow_html=True)

    with st.sidebar.form(key='date_form'):
        st.write('<b>Date Inputs</b>', unsafe_allow_html=True)
        start_date = st.date_input('Choose a start date',
                                     value=datetime(2007,1,1),
                                     min_value=df.date.min(),
                                     max_value=df.date.max(),
                                     key='start')
        end_date = st.date_input('Choose an end date',
                                   value=df.date.max(),
                                   min_value=df.date.min(),
                                   max_value=df.date.max(),
                                   key='end')
        submit_button = st.form_submit_button('Submit', help='Press to recalculate')

    df_date_filter, m, u1, d1, u2, d2 = calc_stds(df, start_date, end_date)

    # chart_placeholder = st.empty()
    st.write("<br>", unsafe_allow_html=True)
    show_lines = st.checkbox('Show mean and standard deviation lines', value=True)

    updated_figure = create_std_graph(df_date_filter, m, u1, d1, u2, d2, show_lines)
    st.plotly_chart(updated_figure, use_container_width=True)

# SECOND PAGE
def adjuted_pe():
    st.title('S&P Price vs P/E Ratio')

    pe_figure = create_inverse_graph(df)

    st.plotly_chart(pe_figure, use_container_width=True)

# NOT USED PAGE FOR LOGIN
def login_info(key="login_info_form"):
    with st.sidebar.form(key=key):
        # col1, space, col2, space2, col3, space3 = st.beta_columns((.3,.02,.3,.02,.2,.2))
        username = st.text_input('Username:',
                                 value="",
                                 type='default')
        password = st.text_input('Password:',
                                 value="",
                                 type='password')
        login_submit_button = st.form_submit_button('Login')

        if username.lower() in logins.login_info.keys():
            if logins.login_info[username.lower()]==password.lower():
                continued = True
                st.success(f'Logged in as {username}')
            else:
                continued = False
                st.warning('Login error. Please try again.')
        else:
            continued = False
            st.warning('Login error. Please try again.')

    return continued

def create_app_with_pages():
    # CREATE PAGES IN APP
    valid_login = login_info()
    if valid_login:
        app = MultiApp()
        app.add_app("Earnings Spread Calculation", earnings_recalc)
        app.add_app("S&P Price vs P/E Ratio", adjuted_pe)
        app.run()

if __name__ == '__main__':

    create_app_with_pages()
