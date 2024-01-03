from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

import input
import partials.modals as modals

def layout():
    return dbc.Container([

        html.Div(children=[],
            id='id-alert-container', 
                style={
                'position': 'absolute',
                'right': 0,
                'marginRight': '2rem',
                'minWidth': '15rem',
                'maxWidth': '15rem',
                'width': '15rem',
                'zIndex': '10001',
                'top': '1rem'},
        ),

        dcc.Store(id='id-store-units', data=input.units),
        dcc.Store(id='id-store-colors', data=input.units_colors),
        dcc.Store(id='id-store-results', data=None),

        dbc.Container([
            # Row 1
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5('Map with units locations and technical information'),
                            html.Div(
                                dcc.Graph(
                                    id='id-graph-map',
                                    config={'modeBarButtonsToRemove': ['lasso2d', 'zoom2d', 'pan2d', 'zoomInGeo', 'zoomOutGeo', 'resetScale2d', 'resetGeo', 'zoom2d', 'toImage'], 'displaylogo': False, },
                                    # className='p-1', 
                                    style={'maxWidth':' 800px', 'margin': 'auto'}
                                    ) 
                            ),

                        ]), className='mb-2 shadow-box'),
                ], xxl=8, className='mb-2', style={'display': 'grid'}),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Unit's geographical coordinates"),
                            html.Div(
                                dag.AgGrid(
                                    id='id-table',   
                                    columnDefs=[
                                        { 'field': 'name', 'sortable': True, 'resizable': True},
                                        { 'field': 'lat', 'type': 'numericColumn', 'editable': False, 'resizable': True},
                                        { 'field': 'lon', 'type': 'numericColumn', 'editable': False, 'resizable': True},
                                        ],
                                    dashGridOptions={'pagination':True, 'paginationAutoPageSize': True, 'rowSelection':'single'},
                                    columnSize='responsiveSizeToFit',
                                    )
                                ),
                        ]), className='mb-2 shadow-box'
                    ), xxl=4, className='mb-2', style={'display': 'grid'}
                ),
            ]), 

            # Row 2
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5('Configuration panel'),
                            html.H6('Change color of unit type:', className='my-3'),
                            html.Div(id='id-div-colors'),
                            html.H6('Calculate power grid:', className='my-3'),
                            html.Div(
                                dbc.Button([
                                        html.I(className='bi bi-power me-2'),
                                        'Run pyomo model',
                                        ],
                                    id='id-run-model',
                                    outline=True, 
                                    color='secondary',
                                    className='d-flex align-items-center'),
                                    className='d-grid gap-2'
                            ),
                            html.H6('Daily costs of running power grid:', className='my-3'),
                            dcc.Loading(html.Div('---', id='id-div-results')),
                        ]), className='mb-2 shadow-box'
                    ), xxl=4, className='mb-2', style={'display': 'grid'}
                ),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5('Unit commitment results'),

                            dcc.Graph(
                                id='id-graph-commitment', 
                                config={'displayModeBar': False},
                                className='p-1'
                                ),                  
                        ]), className='mb-2 shadow-box'),
                ], xxl=8, className='mb-2', style={'display': 'grid'}),
            ]), 
                    
        ], fluid=True, className='p-0'),

        modals.modal_UD,
        modals.modal_C,
        modals.modal_color,

        ], id='id-layout', className='page-container'
    )
