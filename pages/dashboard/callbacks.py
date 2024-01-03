from dash import callback, Output, Input, State, no_update, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash import Patch
import pyomo.environ as pyo
import math

import input
from uc_model import uc_model


min_lat, max_lat = (25, 37)
min_lon, max_lon = (-112.5, -87.5)


def make_alerts(alerts, msg, color):
    ALERT_TIME = 10  # sec
    alerts.append(
        dbc.Alert(
            msg, 
            is_open=True, 
            color=color, 
            duration=ALERT_TIME*1000
            )
        )

    return alerts


@callback(
    Output('id-store-results', 'data'),
    Output('id-div-results', 'children'),
    Output('id-alert-container', 'children'),
    Input('id-run-model', 'n_clicks'),
    State('id-store-units', 'data'),
    State('id-alert-container', 'children'),
    prevent_initial_call=True
)
def run_model(click, units, alerts):
    
    model = uc_model(units, dev=False)
    if not model:

        sys_cost = 'No solution for provided input.'
        
        msg = f'Error during model computation. Check input data.' 
        color = 'warning'
        alerts = make_alerts(alerts, msg, color)

        return None, sys_cost, alerts

    sys_cost = round(pyo.value(model.system_costs), 0)
    sys_cost = f'{sys_cost} $'
    
    msg = f'Model was computed successfully'  
    color = 'success'
    alerts = make_alerts(alerts, msg, color)

    return model.results, sys_cost, alerts


@callback(
    Output('id-table', 'rowData'), 
    Output('id-table', 'getRowStyle'), 
    Input('id-store-units', 'data'),
    Input('id-store-colors', 'data'),
)
def create_grid(units, colors):

    data = []
    for key, value in units.items():
        value['name'] = key
        data.append(value)
    df = pd.DataFrame.from_dict(data)

    df_colors = pd.DataFrame(list( zip( colors.keys(), colors.values() ) ), columns=['type', 'color']) 
    df = df.merge(df_colors, on=['type'])
    data = df.to_dict('records')
    
    getRowStyle = {
        'styleConditions': [
            {
                'condition': f"params.data.name == '{unit['name']}'",
                'style': {'color': unit['color']},
            } for unit in data
        ] 
    }

    return data, getRowStyle


@callback(
    Output('id-graph-map', 'figure', allow_duplicate=True),
    Input('id-table', 'selectedRows'),
    prevent_initial_call=True
)
def create_annotation(row_selected): 

    if row_selected == []:
        return no_update

    patched_figure = Patch()
    lat = (float(row_selected[0]['lat']) - min_lat) / ( max_lat - min_lat )
    lon = (float(row_selected[0]['lon']) - min_lon) / ( max_lon - min_lon )
    text = row_selected[0]['name']
    patched_figure['layout']['annotations'].clear()
    patched_figure['layout']['annotations'].extend(
        [
            dict(
                xref='paper',
                yref='paper',
                x=lon, 
                y=lat,
                text=text,
                showarrow=False,
                bgcolor='white',
                opacity=0.6,
            ),
        ]
    )

    return patched_figure 


@callback(
    Output('id-graph-map', 'figure', allow_duplicate=True),
    Input('id-table', 'cellDoubleClicked'),
    prevent_initial_call=True
)
def delete_annotations(click):
    
    if click is None:
        return no_update

    patched_figure = Patch()
    patched_figure['layout']['annotations'].clear()

    return patched_figure 


@callback(
    Output('id-graph-map', 'figure'),
    Input('id-store-units', 'data'),
    Input('id-store-colors', 'data')
)
def generate_graph_map(units, colors):

    fig = go.Figure()
    for unit in units.keys():
        kind = units[unit]['type']
        fig.add_trace(
            go.Scattergeo(
            lon = [units[unit]['lon']],
            lat = [units[unit]['lat']],
            text = [unit],
            mode = 'markers',
            name = '',
            customdata=[units[unit]['power']],
            showlegend=False,
            hovertemplate='%{text} : %{customdata} MW',
            marker = dict(
                size = units[unit]['power']/10,
                opacity = 0.6,
                reversescale = True,
                autocolorscale = False,
                symbol = 'circle',
                color = colors[kind],
                line = dict(
                    width=1,
                    color='black',
                    ),
                )
            )
        )

    fig.add_trace(
        go.Scattergeo(
            lon=[ ele[0] for ele in input.texas_boundaries ],
            lat=[ ele[1] for ele in input.texas_boundaries ],
            line_color='brown',
            line_width=2,
            mode='lines',
            showlegend=False,
            hoverinfo='none',
            text=[ 'border' for _ in input.texas_boundaries ],
        ))

    fig.update_layout(
            height=375, 
            margin={'r':5,'t':5,'l':5,'b':5},
            geo = dict(
                landcolor = 'rgb(250, 250, 250)',
                oceancolor = '#ccf5ff',
                showcountries=True,
                showlakes=True,
                showland=True,
                showocean=True,
                showrivers=True,
                visible=True, 
                resolution=50, 
                scope='world',
                lataxis={'range': [min_lat, max_lat]},
                lonaxis={'range': [min_lon, max_lon]},
            ), 
        )
    fig.add_annotation(x=0, y=0, text='', showarrow=False)
    
    return fig


@callback(
    Output('id-graph-commitment', 'figure'),
    Input('id-store-results', 'data'),
    Input('id-store-colors', 'data'),
    State('id-store-units', 'data'),
)
def generate_graph_results(results, colors, units):

    sorted_units = sorted( units.items(), key=lambda x: x[1]['vc'])
    sorted_units = dict(sorted_units).keys()

    fig = go.Figure()
    for unit in sorted_units:
        if results is None:
            break
        if unit not in results.keys():
            continue

        x = results[unit].keys()  # each hour
        y = results[unit].values()  # each hour
        kind = units[unit]['type']

        fig.add_trace(
            go.Bar(
                x=list(x),
                y=list(y),
                name=unit,
                marker=dict(color=colors[kind], opacity=0.6, line=dict(width=0.5, color='black')),
                hovertemplate='Power: %{y} MW',
                showlegend=False
            )
        )
    fig.update_layout(
        barmode='relative',
        bargap=0,
        plot_bgcolor='white',
        height=250, 
        margin={'r':5,'t':5,'l':5,'b':5},
    )
    fig.update_xaxes(
        tickfont=dict(size=11),
        linewidth=1,
        linecolor='black',
        ticks='outside',
        mirror=True
    )
    fig.update_yaxes(
        title=dict(text='Power [MW]', font=dict(size=14)),
        tickfont=dict(size=11),
        linewidth=1,
        linecolor='black',
        ticks='outside',
        mirror=True
    )
    if results is None:
        fig.add_annotation(
            text='To see results run pyomo model first',
            xref='paper', 
            yref='paper',
            x=0.5, 
            y=0.5, 
            showarrow=False
            )
    
    return fig


@callback(
    Output('id-modal-update-delete-unit', 'is_open', allow_duplicate=True),
    Output('id-store-units', 'data', allow_duplicate=True), 
    Output('id-alert-container', 'children', allow_duplicate=True),
    Input('id-button-delete', 'n_clicks'),
    State('id-store-units', 'data'), 
    State('id-modal-update-delete-unit-header', 'children'),
    State('id-alert-container', 'children'),
    prevent_initial_call=True
)
def delete_unit(click, data, name, alerts):

    del data[name]

    msg = f'Deleted unit: {name}'
    color = 'info'
    alerts = make_alerts(alerts, msg, color)

    return False, data, alerts


@callback(
    Output('id-modal-update-delete-unit', 'is_open', allow_duplicate=True),
    Output('id-store-units', 'data', allow_duplicate=True), 
    Input('id-button-update', 'n_clicks'),
    State('id-store-units', 'data'), 
    State('id-modal-update-delete-unit-header', 'children'),
    State('id-input-update-power', 'value'),
    State('id-input-update-vc', 'value'),
    State('id-input-update-lat', 'value'),
    State('id-input-update-lon', 'value'),
    State('id-input-update-ramp', 'value'),
    prevent_initial_call=True
)
def update_unit(click, data, name, power, vc, lat, lon, ramp):

    # Error handling
    def check_pos_number(new_value, old_value):
        try:
            value = math.fabs(float(new_value))
        except ValueError:
            value = old_value
        return value

    data[name]['power'] = check_pos_number(power, data[name]['power'])
    data[name]['vc'] = check_pos_number(vc, data[name]['vc'])
    data[name]['lat'] = lat
    data[name]['lon'] = lon
    data[name]['ramp'] = check_pos_number(ramp, data[name]['ramp'])

    return False, data


@callback(
    Output('id-modal-create-unit', 'is_open', allow_duplicate=True),
    Output('id-store-units', 'data', allow_duplicate=True), 
    Output('id-graph-map', 'clickData', allow_duplicate=True),
    Output('id-input-create-name', 'value', allow_duplicate=True),
    Input('id-button-create', 'n_clicks'),
    State('id-store-units', 'data'), 
    State('id-input-create-name', 'value'),
    State('id-input-create-type', 'value'),
    State('id-input-create-power', 'value'),
    State('id-input-create-vc', 'value'),
    State('id-input-create-lat', 'value'),
    State('id-input-create-lon', 'value'),
    State('id-input-create-ramp', 'value'),
    prevent_initial_call=True
)
def create_unit(click, data, name, kind, power, vc, lat, lon, ramp):

    # Error handling
    def check_pos_number(new_value, default_value=0):
        try:
            value = math.fabs(float(new_value))
        except ValueError:
            value = default_value
        return value

    new_unit = {
        'type': kind, 
        'lat': lat, 
        'lon': lon, 
        'power': check_pos_number(power), 
        'vc': check_pos_number(vc), 
        'ramp': check_pos_number(ramp), 
    }
    data[name] = new_unit
    
    return False, data, None, None


@callback(
    Output('id-button-create', 'disabled'),
    Input('id-input-create-name', 'value'),
    State('id-store-units', 'data'), 
    prevent_initial_call=True
)
def check_unit_name(text, data):

    if text is None or len(text) < 3 or text in data.keys():
        return True
    return False


@callback(
    Output('id-graph-map', 'clickData'),
    Output('id-modal-update-delete-unit', 'is_open'),
    Output('id-modal-update-delete-unit-header', 'children'),
    Output('id-input-update-power', 'value'),
    Output('id-input-update-vc', 'value'),
    Output('id-input-update-lat', 'value'),
    Output('id-input-update-lon', 'value'),
    Output('id-input-update-ramp', 'value'),
    Input('id-graph-map', 'clickData'),
    State('id-store-units', 'data'), 
    prevent_initial_call=True
)
def open_modal_update_delete_unit(clickData, units):
    
    if clickData is None:
        raise PreventUpdate
    if clickData['points'][0]['text'] == 'border':
        raise PreventUpdate

    unit = clickData['points'][0]['text']
    power = units[unit]['power']
    vc = units[unit]['vc']
    vc = 0 if np.isnan(vc) else vc
    lat = units[unit]['lat']
    lon = units[unit]['lon']
    ramp = units[unit]['ramp']
    ramp = 0 if np.isnan(ramp) else ramp

    return None, True, unit, power, vc, lat, lon, ramp


@callback(
    Output('id-graph-map', 'selectedData'),
    Output('id-modal-create-unit', 'is_open'),
    Output('id-input-create-lat', 'value'),
    Output('id-input-create-lon', 'value'),
    Input('id-graph-map', 'selectedData'),
    prevent_initial_call=True
)
def open_modal_create_unit(select):
    
    if select is None or 'range' not in select.keys():
        raise PreventUpdate
    
    rectangle = select['range']['geo']
    lon = round( 0.5 * ( rectangle[0][0] + rectangle[1][0] ), 2 )
    lat = round( 0.5 * ( rectangle[0][1] + rectangle[1][1] ), 2 )
    
    return None, True, lat, lon


@callback(
    Output('id-div-colors', 'children'),
    Input('id-store-colors', 'data')
)
def generate_colors_div(colors):
    
    lst = []
    for key, value in colors.items():
        lst.append(
            dbc.Button(
                key.title(),
                id={'index': f'id-button-color-{key}', 'type': 'change-color'},
                style={'color': value,},
                color='link'
            )
        )

    return lst


@callback(
    Output('id-modal-change-color', 'is_open'),
    Output('id-modal-change-color-header', 'children'),
    Output('id-color-picker', 'value'),
    Output('id-modal-change-color-unit-name', 'children'),
    Input({'type': 'change-color', 'index': ALL}, 'n_clicks'),
    State('id-store-colors', 'data'),
    prevent_initial_call=True
)
def open_modal_color_change(clicks, colors):

    if not any(clicks):
        raise PreventUpdate

    unit_clicked = ctx.triggered_id['index'].split('-')[-1]
    color = colors[unit_clicked]
    text = f'Change color of: {unit_clicked.title()}'

    return True, text, dict(hex=color), unit_clicked


@callback(
    Output('id-modal-change-color', 'is_open', allow_duplicate=True),
    Output('id-store-colors', 'data'),
    Input('id-button-change-color-save', 'n_clicks'),
    State('id-modal-change-color-unit-name', 'children'),
    State('id-color-picker', 'value'),
    State('id-store-colors', 'data'),
    prevent_initial_call=True
)
def save_color(click, unit, value, colors):

    color = value['hex']
    colors[unit] = color

    return False, colors
