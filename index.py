import dash
import dash_bootstrap_components as dbc
from waitress import serve


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    use_pages=True
    )

app.layout = dbc.Container([
    dbc.NavbarSimple([
        dbc.NavItem(dbc.NavLink('Home', href='/')),
        dbc.NavItem(dbc.NavLink('Dashboard', href='dashboard')),
    ],
    brand='Unit Commitment App',
    brand_href='/',
    color='secondary',
    dark=True,
    className='px-4',
    ),    
    dash.page_container
], className='main-container'
)


# if __name__ == '__main__':
#     app.run(debug=True)

serve(app.server, port=8080)