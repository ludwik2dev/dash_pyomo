from dash import html, dcc
import dash_bootstrap_components as dbc
import input
import dash_daq as daq


modal_UD = dbc.Modal([

    dbc.ModalHeader(dbc.ModalTitle('Header', id='id-modal-update-delete-unit-header')),

    dbc.ModalBody([

        dbc.Form([
            dbc.Row([
                    dbc.Label('Power', width=3, html_for='id-input-update-power'),
                    dbc.Col(
                        dbc.Input(id='id-input-update-power', type='number'),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Variable cost', width=3, html_for='id-input-update-vc'),
                    dbc.Col(
                        dbc.Input(id='id-input-update-vc', type='number'), 
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Ramp', width=3, html_for='id-input-update-ramp'),
                    dbc.Col(
                        dbc.Input(id='id-input-update-ramp', type='number'),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Latitude', width=3, html_for='id-input-update-lat'),
                    dbc.Col(
                        dbc.Input(id='id-input-update-lat', type='number', disabled=True),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Longitude', width=3, html_for='id-input-update-lon'),
                    dbc.Col(
                        dbc.Input(id='id-input-update-lon', type='number', disabled=True),
                        width=9,
                    )], className='mb-3')
        ], id='id-form-create')

    ], id='id-modal-body'
    ),        
    dbc.ModalFooter([
        dbc.Button('Delete', id='id-button-delete', n_clicks=0, color='danger'),
        dbc.Button('Update', id='id-button-update',  n_clicks=0, color='success'),
    ]),

],

    id='id-modal-update-delete-unit',
    is_open=False,
)


modal_C = dbc.Modal([

    dbc.ModalHeader(dbc.ModalTitle('Create new unit')),

    dbc.ModalBody([

        dbc.Form([
            dbc.Row([
                    dbc.Label('Unit name', width=3, html_for='id-input-create-name'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-name', type='text', placeholder='Name must be unique'),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Unit type', width=3, html_for='id-input-create-type'),
                    dbc.Col(
                        dcc.Dropdown(options=input.unit_types, value='coal', clearable=False, id='id-input-create-type'),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Power', width=3, html_for='id-input-create-power'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-power', type='number', value=100),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Variable cost', width=3, html_for='id-input-create-vc'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-vc', type='number', value=1), 
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Ramp', width=3, html_for='id-input-create-ramp'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-ramp', type='number', value=10),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Latitude', width=3, html_for='id-input-create-lat'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-lat', type='number', disabled=True),
                        width=9,
                    )], className='mb-3'),
            dbc.Row([
                    dbc.Label('Longitude', width=3, html_for='id-input-create-lon'),
                    dbc.Col(
                        dbc.Input(id='id-input-create-lon', type='number', disabled=True),
                        width=9,
                    )], className='mb-3')
        ])

    ], 
    ),        
    dbc.ModalFooter([
        dbc.Button('Create', id='id-button-create', n_clicks=0, color='success', disabled=True),
    ]),

],

    id='id-modal-create-unit',
    is_open=False,
)


modal_color = dbc.Modal([

    dbc.ModalHeader(dbc.ModalTitle(id='id-modal-change-color-header')),

    dbc.ModalBody([

        daq.ColorPicker(
            id='id-color-picker',
        ),
        html.Div(id='id-modal-change-color-unit-name', style={'display': 'none'})
    ], style={'margin': 'auto'}
    ),        
    dbc.ModalFooter([
        dbc.Button('Save', id='id-button-change-color-save', n_clicks=0, color='success'),
    ]),

],

    id='id-modal-change-color',
    is_open=False,
)