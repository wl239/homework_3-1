import time

import dash
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from ibapi.contract import Contract
from ibapi.order import Order
from fintech_ibkr import *
from dash import dcc
from dash import html, dash_table
import dash_daq as daq
from datetime import date

# Make a Dash app!
app = dash.Dash(__name__)
df = pd.read_csv('submitted_orders.csv')
# Define the layout.
app.layout = html.Div([
    html.Div(
        id='sync-connection-status',
        children='False',
        style={'display': 'none'}
    ),
    # Section title
    html.H2("Section 1: Fetch & Display exchange rate historical data"),
    html.Div([
        html.H3("Select value for whatToShow:"),
        html.Div(
            dcc.Dropdown(
                ["MIDPOINT", "BID", "ASK", "BID_ASK", "HISTORICAL_VOLATILITY"],
                "MIDPOINT",
                id='what-to-show'
            ),
            style={'width': '300px'}
        ),
        html.Br(),
        html.H3("Select value for endDateTime:"),
        html.Div(
            children=[
                html.P(
                    "You may select a specific endDateTime for the call to fetch_historical_data. " +
                    "If any of the below is empty, the current present moment will be used."
                )
            ],
            style={'width': '490px'}
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label('Date:'),
                        dcc.DatePickerSingle(id='edt-date')
                    ],
                ),
                html.Br(),
                html.Div(
                    children=[
                        html.Label('Hour:'),
                        dcc.Dropdown(list(range(24)), id='edt-hour'),
                    ],
                    style={
                        'width': '15%',
                        'display': 'inline-block',
                        'padding-right': '15px'
                    }
                ),
                html.Div(
                    children=[
                        html.Label('Minute:'),
                        dcc.Dropdown(list(range(60)), id='edt-minute'),
                    ],
                    style={
                        'width': '15%',
                        'display': 'inline-block',
                        'padding-right': '15px'
                    }
                ),
                html.Div(
                    children=[
                        html.Label('Second:'),
                        dcc.Dropdown(list(range(60)), id='edt-second'),
                    ],
                    style={'width': '15%', 'display': 'inline-block'}
                )
            ]
        ),
        html.Br(),
        html.H3(
            "Select value for barSizeSetting:",
            style={'display': 'inline-block'}
        ),
        dcc.Dropdown(
            options=[
                '1 secs', '5 secs', '10 secs', '15 secs', '30 secs', '1 min',
                '2 mins', '3 mins',	'5 mins', '10 mins', '15 mins',
                '20 mins', '30 mins', '1 hour',	'2 hours',	'3 hours',
                '4 hours', '8 hours',  '1 day', '1 week', '1 month'
            ],
            id='bar-size',
            value='1 hour',
            style={
                'width': '100px',
                'display': 'inline-block',
                'vertical-align': 'middle',
                'padding-left': '15px'
            }
        ),
        html.Br(),
        html.H3("Select value for durationStr:"),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label('Amount:'),
                        dcc.Input(
                            id='duration-amount',
                            value=30,
                            type='number',
                            style={'display': 'inline-block', 'width': '75px'}
                        )
                    ],
                    style={
                        'display': 'inline-block',
                        'margin-right': '20px',
                    }
                ),
                html.Div(
                    children=[
                        html.Label('Unit:', style={'display': 'inline-block'}),
                        dcc.Dropdown(
                            options = [
                                {'label': 'Seconds', 'value': 'S'},
                                {'label': 'Days', 'value': 'D'},
                                {'label': 'Weeks', 'value': 'W'},
                                {'label': 'Months', 'value': 'M'},
                                {'label': 'Years', 'value': 'Y'}
                            ],
                            id='duration-unit',
                            value='D',
                            style={
                                'width': '75px',
                                'display': 'inline-block',
                                'vertical-align': 'middle'
                            }
                        ),
                    ],
                    style={
                        'display': 'inline-block',
                        'padding-right': '5px',
                        'vertical-align': 'middle'
                    }
                )
            ]
        ),
        html.Br(),
        html.H3("Use RTH?", style={'display': 'inline-block'}),
        html.Div(
            children=[
                html.P("NO", style={'display': 'inline-block'}),
                daq.ToggleSwitch(
                    id='use-rth',
                    value=False,
                    style={'display': 'inline-block'}
                ),
                html.P("YES", style={'display': 'inline-block'}),
            ],
            style={'display': 'inline-block', 'padding-left': '10px'}
        ),
        html.Br(),
        html.H3("Enter a currency pair:"),
        html.P(
            children=[
                "See the various currency pairs here: ",
                html.A(
                    "currency pairs",
                    href=('https://www.interactivebrokers.com/en/index.php?f'
                          '=2222&exch=ibfxpro&showcategories=FX')
                )
            ]
        ),
        # Currency pair text input, within its own div.
        html.Div(
            # The input object itself
            ["Input Currency: ", dcc.Input(
                id='currency-input', value='AUD.CAD', type='text'
            )],
            # Style it so that the submit button appears beside the input.
            style={'display': 'inline-block', 'padding-top': '5px'}
        ),
        # Submit button
        html.Button('Submit', id='submit-button', n_clicks=0),
        html.Br(),
        html.Br(),
        # Div for initial instructions and the updated info once submit is pressed
        html.Div(
            id='currency-output',
            children='Enter a currency code and press submit'),
    ],
        style={'width': '550px', 'display': 'inline-block'}
    ),
    html.Div([
        html.Div([
            html.Div([
                html.H3(
                    'Hostname: ',
                    style={'display': 'inline-block', 'margin-right': 20}
                ),
                dcc.Input(
                    id='host',
                    value='127.0.0.1',
                    type='text',
                    style={'display': 'inline-block'}
                )],
                style={'display': 'inline-block'}
            ),
            html.Div([
                html.H3(
                    'Port: ',
                    style={'display': 'inline-block', 'margin-right': 59}
                ),
                dcc.Input(
                    id='port',
                    value='7497',
                    type='text',
                    style={'display': 'inline-block'}
                )],
                style = {'display': 'inline-block'}
            ),
            html.Div([
                html.H3(
                    'Client ID: ',
                    style={'display': 'inline-block', 'margin-right': 27}
                ),
                dcc.Input(
                    id='clientid',
                    value='10645',
                    type='text',
                    style={'display': 'inline-block'}
                )
            ],
                style={'display': 'inline-block'}
            )
        ]
        ),
        html.Br(),
        html.Button('TEST SYNC CONNECTION', id='connect-button', n_clicks=0),
        html.Div(id='connect-indicator'),
        html.Div(id='contract-details')
    ],
        style={'width': '405px', 'display': 'inline-block',
               'vertical-align': 'top', 'padding-left': '15px'}
    ),
    # Line break
    html.Br(),
    # Div to hold the candlestick graph
    dcc.Loading(
        id="loading-1",
        type="circle", color='#7BC043',
        children=html.Div([dcc.Graph(id='candlestick-graph')])
    ),
    # Another line break
    html.Br(),
    # Section title
    html.H2("Section 2: Make a trade"),
    # Div to confirm what trade was made
    html.Div(id='trade-output'),
    html.Div(
        children=[
            html.Label('Choose type:'),
            dcc.Dropdown(
                options=[
                    {'label': 'Stock', 'value': "STK"},
                    {'label': 'FX Pairs', 'value': 'CASH'},
                    {'label': 'Crypto', 'value': 'CRYPTO'},
                    {'label': 'Bond', 'value': 'BOND'},
                    {'label': 'Fund', 'value': 'FUND'}],
                id='sec-type',
                value='STK'
            ),
        ],
        style={
            'width': '150px'
        }
    ),
    html.Br(),
    html.Div(
        children=[
            html.Label('Enter the Asset Symbol:'),
            dcc.Input(
                id='contract-symbol',
                value='SPY',
                type='text',
            )
        ],
        style={
            'display': 'inline-block',
        }
    ),
    html.Br(),
    html.Br(),
    html.Div(
        children=[
            html.Label('Enter the Currency:'),
            dcc.Input(
                id='currency',
                value='USD',
                type='text',
            )
        ],
        style={
            'display': 'inline-block',
        }
    ),
    html.Br(),
    html.Br(),
    html.Div(
        children=[
            html.Label('Enter the Exchange:'),
            dcc.Input(
                id='exchange',
                value='SMART',
                type='text',
            )
        ],
        style={
            'display': 'inline-block',
        }
    ),
    html.Br(),
    html.Br(),
    html.Div(
        children=[
            html.Label('Enter the Primary Exchange:'),
            dcc.Input(
                id='primary-exchange',
                value='ARCA',
                type='text',
            )
        ],
        style={
            'display': 'inline-block',

        }
    ),
    html.Br(),
    html.Br(),
    # market order or limit order
    html.Div(
        children=[
            html.Div(
                children=[
                    dcc.RadioItems(
                        id='mkt-or-lmt',
                        options=[
                            {'label': 'Market', 'value': 'MKT'},
                            {'label': 'Limit', 'value': 'LMT'}
                        ],
                        value='MKT'
                    )
                ],
            ),
            html.Div(
                children=[
                    # Radio items to select buy or sell
                    dcc.RadioItems(
                        id='buy-or-sell',
                        options=[
                            {'label': 'BUY', 'value': 'BUY'},
                            {'label': 'SELL', 'value': 'SELL'}
                        ],
                        value='BUY'
                    )
                ],
            ),
            html.Br(),
            html.Div(
                children=[
                    html.Label('Enter limit price:'),
                    dcc.Input(
                        id='limit-price',
                        type='number',
                    )
                ],
            ),
        ]
    ),
    html.Br(),
    # Numeric input for the trade amount
    html.Div(
        children=[
            html.Label('Enter the Trade Amount:'),
            dcc.Input(
                id='trade-amt',
                value='200',
                type='number',
            )
        ],
        style={
            'display': 'inline-block',
        }
    ),
    html.Br(),
    html.Br(),
    # Submit button for the trade
    html.Button('Trade', id='trade-button', n_clicks=0),
    html.Br(),
    html.Br(),
    dash_table.DataTable(df.to_dict('records')),  #, [{"name": i, "id": i} for i in df.columns], id='table')
    html.Br()
])

@app.callback(
    [
        Output("connect-indicator", "children"),
        Output("sync-connection-status", "children")
    ],
    Input("connect-button", "n_clicks"),
    [State("host", "value"), State("port", "value"), State("clientid", "value")]
)
def update_connect_indicator(n_clicks, host, port, clientid):
    try:
        managed_accounts = fetch_managed_accounts(host, port, clientid)
        message = "Connection successful! Managed accounts: " + ", ".join(managed_accounts)
        sync_connection_status = "True"
    except Exception as inst:
        x, y, z = inst.args
        message = "Error in " + x + ": " + y + ". " + z
        sync_connection_status = "False"
    return message, sync_connection_status

@app.callback(
    [ # there's more than one output here, so you have to use square brackets to
        # pass it in as an array.
        Output(component_id='currency-output', component_property='children'),
        Output(component_id='candlestick-graph', component_property='figure')
    ],
    Input('submit-button', 'n_clicks'),
    # The callback function will run when the submit button's n_clicks
    #   changes because the user pressed "submit".
    # The currency input's value is passed in as a "State" because if the user
    #   is typing and the value changes, then the callback function won't run.
    # But when the callback does run because the submit button was pressed,
    #   then the value of 'currency-input' at the time the button was pressed
    #   DOES get passed in to the function.
    [State('currency-input', 'value'), State('what-to-show', 'value'),
     State('edt-date', 'date'), State('edt-hour', 'value'),
     State('edt-minute', 'value'), State('edt-second', 'value'),
     State('sync-connection-status', 'children'), State('bar-size', 'value'),
     State('use-rth', 'value'), State('duration-amount', 'value'),
     State('duration-unit', 'value'), State('host', 'value'),
     State('port', 'value'),
     State('clientid', 'value')],
    prevent_initial_call = True
)
def update_candlestick_graph(n_clicks, currency_string, what_to_show,
                             edt_date, edt_hour, edt_minute, edt_second,
                             conn_status, bar_size, use_rth, duration_amount,
                             duration_unit, host, port, clientid):
    if not bool(conn_status):
        return '', go.Figure()

    # First things first -- what currency pair history do you want to fetch?
    # Define it as a contract object!
    contract = Contract()
    contract.symbol = currency_string.split(".")[0]
    contract.secType  = 'CASH'
    contract.exchange = 'IDEALPRO' # 'IDEALPRO' is the currency exchange.
    contract.currency = currency_string.split(".")[1]

    try:
        contract_details = fetch_contract_details(contract, hostname=host, port=port, client_id=clientid)
    except:
        return ("No contract found for " + currency_string), go.Figure()

    contract_symbol_ibkr = contract_details.symbol[0]+'.'+contract_details.currency[0]

    # If the contract name doesn't equal the one you want:
    if not contract_symbol_ibkr == currency_string:
        return ("Requested contract: " + currency_string + " but received " +
                "contract: " + contract_symbol_ibkr), go.Figure()

    if any([i is None for i in [edt_date, edt_hour, edt_minute, edt_second]]):
        endDateTime = ''
    else:
        endDateTime = str(edt_date).replace("-","") + " " + \
                      '{:0>2}'.format(edt_hour) + ":" + \
                      '{:0>2}'.format(edt_hour) + ":" + \
                      '{:0>2}'.format(edt_minute)

    # time.sleep(5)

    ############################################################################
    ############################################################################
    # This block is the one you'll need to work on. UN-comment the code in this
    #   section and alter it to fetch & display your currency data!
    # Make the historical data request.
    # Where indicated below, you need to make a REACTIVE INPUT for each one of
    #   the required inputs for req_historical_data().
    # This resource should help: https://dash.plotly.com/dash-core-components

    # Some default values are provided below to help with your testing.
    # Don't forget -- you'll need to update the signature in this callback
    #   function to include your new vars!
    cph = fetch_historical_data(
        contract=contract,
        endDateTime=endDateTime,
        durationStr=str(duration_amount) + " " + duration_unit,
        barSizeSetting=bar_size,
        whatToShow=what_to_show,
        useRTH=use_rth,
        hostname=host,
        port=port,
        client_id=clientid
    )
    # # Make the candlestick figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=cph['date'],
                open=cph['open'],
                high=cph['high'],
                low=cph['low'],
                close=cph['close']
            )
        ]
    )
    # # Give the candlestick figure a title
    fig.update_layout(
        title=('Exchange Rate: ' + currency_string + ': ' + what_to_show)
    )
    ############################################################################
    ############################################################################

    currency_string = "fetched data for: " + contract_symbol_ibkr

    # Return your updated text to currency-output, and the figure to
    #   candlestick-graph outputs
    return currency_string, fig

# Callback for what to do when trade-button is pressed
@app.callback(
    # We're going to output the result to trade-output
    Output(component_id='trade-output', component_property='children'),
    # Only run this callback function when the trade-button is pressed
    Input('trade-button', 'n_clicks'),
    # We DON'T want to run this function whenever buy-or-sell, trade-currency,
    #   or trade-amt is updated, so we pass those in as States, not Inputs:
    [State('sec-type','value'), State('contract-symbol', 'value'), State('currency','value'),
     State('exchange', 'value'), State('primary-exchange', 'value'), State('mkt-or-lmt', 'value'),
     State('buy-or-sell', 'value'), State('limit-price', 'value'),
     State('trade-amt', 'value'), State("host", "value"),
     State("port", "value"), State("clientid", "value")],
    # DON'T start executing trades just because n_clicks was initialized to 0!!!
    prevent_initial_call=True
)
def trade(n_clicks, sec_type, contract_symbol, currency, exchange, primary_exchange,
          mkt_or_lmt, action, limit_price, trade_amt, host, port, clientid):
    # Still don't use n_clicks, but we need the dependency

    # Make the message that we want to send back to trade-output
    msg = action + ' ' + str(trade_amt) + ' ' + contract_symbol
    contract = Contract()
    contract.symbol = contract_symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    if primary_exchange is not None:
        contract.primaryExchange = primary_exchange

    order = Order()
    order.action = action
    order.orderType = mkt_or_lmt
    order.totalQuantity = trade_amt

    if mkt_or_lmt == 'LMT':
        if limit_price is None:
            return "Invalid Limit price"
        order.lmtPrice = limit_price

    fetch_contract_details(contract)

    allInfo = place_order(contract, order)
    # order_id = allInfo['order_id'][0]
    time = fetch_current_time(host, port, clientid)    # fetch_current_time()
    # client_id = allInfo['client_id'][0]
    perm_id = allInfo['perm_id'][0]

    trade_data = {
        'timestamp': time,
        'order_id': order.orderId,
        'client_id': clientid,
        'perm_id': perm_id,
        'con_id': contract.conId,
        'symbol': contract.symbol,
        'action': action,
        'size': trade_amt,
        'order_type': order.orderType,
        'lmt_price': limit_price
    }

    file_path = 'submitted_orders.csv'
    df_file = pd.read_csv(file_path, index_col=0)
    index = ['timestamp', 'order_id', 'client_id', 'perm_id',
             'con_id', 'symbol', 'action', 'size', 'order_type', 'lmt_price']
    df_file = pd.concat([df_file, pd.DataFrame(trade_data, index=[0])], ignore_index=True).set_index(index)
    df_file.to_csv(file_path)

    print("Successful!")

    # Return the message, which goes to the trade-output div's children
    return msg, df_file.to_dict('records')

# Run it!
if __name__ == '__main__':
    app.run_server(debug=True)
