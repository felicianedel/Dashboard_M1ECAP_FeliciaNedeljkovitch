# PACKAGES -------------------------------------------------------------------------
import pandas as pd
import plotly.graph_objects as go 
import calendar as cal
import plotly.express as px

#DONNNEES --------------------------------------------------------------------------
df = pd.read_csv("data.csv")
df = df[["CustomerID", "Gender", "Location", "Product_Category", "Quantity", "Avg_Price", "Transaction_Date",
  "Month", "Discount_pct"]]
df["CustomerID"]=df["CustomerID"].fillna(0).astype(int)
df["Transaction_Date"]=pd.to_datetime(df["Transaction_Date"])
df["Total_price"]= df["Quantity"]*df["Avg_Price"]*(1-df["Discount_pct"]/100)

#FONCTIONS -------------------------------------------------------------------------
## CHIFFRE D'AFFAIRES ----
def calculer_chiffre_affaire(data):
    return data["Total_price"].sum()
ca = calculer_chiffre_affaire(df)

## FREQUENCE MEILLEURE VENTE ----
def frequence_meilleure_vente(data, top=10, ascending=False):
    freq = data.groupby("Product_Category")["Quantity"].sum().sort_values(ascending=ascending)
    return freq.head(top)
top=frequence_meilleure_vente(df, top=10, ascending= False).reset_index()

## INDICATEUR DU MOIS ----
def indicateur_du_mois(data, current_month=12, freq=True, abbr=False):
    data_mois = data[data["Month"] == current_month] #on garde uniquement le mois 12
    if freq:
        result = data_mois["Quantity"].sum() #on compte la quantité vendue(pour freq=True)
        indicateur = "Quantités vendues"
    else:
        result = data_mois["Total_price"].sum() #on compte le chiffre d'affaire (si jamais on met freq=False)
        indicateur = "Chiffre d'affaires"
    
    if abbr:
        month_name=cal.month_abbr[current_month]
    else:
        month_name = cal.month_name[current_month]
    
    return {"mois": month_name,"valeur":result, "indicateur":indicateur}
resultat = indicateur_du_mois(df, 12, True, False)

# GRAPHIQUES -------------------------------------------------------------
##BARPLOT ----
def barplot_top_10_ventes(data):
    top = frequence_meilleure_vente(data, top=10, ascending=False).reset_index()
    data_top = data[data["Product_Category"].isin(top["Product_Category"])]
    ventes = data_top.groupby(["Product_Category", "Gender"])["Quantity"].sum().reset_index()
    fig = px.bar(
        ventes,
        x="Quantity",
        y="Product_Category",
        color="Gender",
        barmode="group",
        title="Top 10 des meilleures ventes par genre",
        labels={
            "Product_Category": "Catégorie de produits",
            "Quantity": "Quantité vendue",
            "Gender": "Genre"
        },
        category_orders={
            "Product_Category": top["Product_Category"].tolist()
        }
    )
    return fig
barplot_top_10_ventes(df)

## EVOLUTION CHIFFRE D'AFFAIRES----
def plot_evolution_chiffre_affaire(data):
    data = data.set_index("Transaction_Date")
    evolution = data["Total_price"].resample("W").sum().reset_index() #W = Week
    fig = px.line(
        evolution,
        x="Transaction_Date",
        y="Total_price",
        title="Evolution du chiffre d'affaire par semaine",
        labels={
        "Transaction_Date": "Semaine",
        "Total_price": "Chiffre d'affaire"
        }
    )
    fig.update_layout(
    margin=dict(l=10, r=10, t=30, b=10)
)
    return fig
plot_evolution_chiffre_affaire(df)

## INDICATEUR CA ----
def plot_chiffre_affaire_mois(data, current_month=12):
    mois_courant = indicateur_du_mois(data, current_month=current_month, freq=False, abbr=False)
    mois_precedent = indicateur_du_mois(data, current_month=current_month-1, freq=False, abbr=False)
    fig = go.Figure()
    fig.add_trace(
        go.Indicator(
            value=mois_courant["valeur"],
            mode="number+delta",
            delta={"reference": mois_precedent["valeur"]},
            title={"text": f"{mois_courant['indicateur']} - {mois_courant['mois']}"}
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig
plot_chiffre_affaire_mois(df, 12)

## INDICATEUR QUANTITES VENDUES----
def plot_vente_mois(data, current_month=12, abbr=False):
    mois_courant = indicateur_du_mois(data, current_month=current_month, freq=True, abbr=abbr)
    mois_precedent = indicateur_du_mois(data, current_month=current_month-1, freq=True, abbr=abbr)
    fig = go.Figure()
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=mois_courant["valeur"],
            delta={"reference": mois_precedent["valeur"]},
            title={"text": f"{mois_courant['indicateur']} - {mois_courant['mois']}"}
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig
plot_vente_mois(df, 12, False)

## TABLEAU 100 VENTES ----
df_last_100 = df.sort_values("Transaction_Date", ascending=False).head(100)
df_last_100["Transaction_Date"] = pd.to_datetime(df_last_100["Transaction_Date"]).dt.strftime("%Y-%m-%d")
df_last_100 = df_last_100[
    ["Transaction_Date", "Gender", "Location", "Product_Category",
     "Quantity", "Avg_Price", "Discount_pct"]
]


# TABLEAU DE BORD -------------------------------------------------------------
import dash
from dash import dcc, Input, Output, dash_table, html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    # HEADER
    dbc.Row([
        dbc.Col(
            html.H2(
                "ECAP Store",
                style={
                    "margin": "0",
                    "fontWeight": "bold",
                    "fontSize": "24px"
                }
            ),
            md=6,
            style={
                "display": "flex",
                "alignItems": "center",
                "height": "100%"
            }
        ),
        dbc.Col(
            dcc.Dropdown(
                id="filtre_location",
                options=[
                    {"label": loc, "value": loc}
                    for loc in sorted(df["Location"].dropna().astype(str).unique())
                ],
                placeholder="Choisissez des zones",
                multi=True,
                style={"fontSize": "14px"}
            ),
            md=6,
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "height": "100%"
            }
        )
    ],
    className="g-0",
    style={
        "backgroundColor": "#b9dbea",
        "height": "7vh",
        "padding": "0 8px"
    }),

    # CONTENU
    dbc.Row([
        # COLONNE GAUCHE ----------------------------------------------------------------
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id="kpi_ca",
                        figure=plot_chiffre_affaire_mois(df, 12),
                        config={"displayModeBar": False},
                        style={"height": "100%", "width": "100%"}
                    ),
                    md=6,
                    style={"height": "22vh", "padding": "0"}
                ),
                dbc.Col(
                    dcc.Graph(
                        id="kpi_ventes",
                        figure=plot_vente_mois(df, 12, False),
                        config={"displayModeBar": False},
                        style={"height": "100%", "width": "100%"}
                    ),
                    md=6,
                    style={"height": "22vh", "padding": "0"}
                ),
            ], className="g-0", style={"marginTop": "0.3vh"}),

            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id="top10ventes",
                        figure=barplot_top_10_ventes(df),
                        config={"displayModeBar": False},
                        style={"height": "100%", "width": "100%"}
                    ),
                    md=12,
                    style={"height": "70vh", "padding": "0", "marginTop": "0.3vh"}
                )
            ], className="g-0")
        ], md=6, style={"padding": "0"}),

        # COLONNE DROITE -------------------------------------------------------------
        ## GRAPHIQUE EVOLUTION CA 
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id="graph_CA",
                        figure=plot_evolution_chiffre_affaire(df),
                        config={"displayModeBar": False},
                        style={"height": "100%", "width": "100%"}
                    ),
                    md=12,
                    style={"height": "40vh", "padding": "0", "marginTop": "0.3vh"}
                )
            ], className="g-0"),
             
            ## TABLEAU DES 100 DERNIERES VENTES 
            dbc.Row([
                dbc.Col([
                    html.H5(
                        "Table des 100 dernières ventes",
                        style={
                            "margin": "3px 0"
                        }
                    ),

                    dash_table.DataTable(
                        id="table_ventes",
                        data=df_last_100.to_dict("records"),
                        columns=[
                            {"name": "Date", "id": "Transaction_Date"},
                            {"name": "Gender", "id": "Gender"},
                            {"name": "Location", "id": "Location"},
                            {"name": "Product_Category", "id": "Product_Category"},
                            {"name": "Quantity", "id": "Quantity"},
                            {"name": "Avg_Price", "id": "Avg_Price"},
                            {"name": "Discount_Pct", "id": "Discount_pct"},
                        ],

                        page_size=5,              #nb de lignes affichées
                        page_action="native",
                        sort_action="native",
                        filter_action="native",

                        style_table={
                             "width": "100%",
                             "borderCollapse": "collapse"
                             },

                        style_cell={
                            "textAlign": "center",
                            "fontSize": "8px",
                            "whiteSpace": "nowrap",
                            "fontFamily": "monospace",
                            "lineHeight": "9px",
                            "padding": "0px",   # presque aucun padding
                            "height": "9px",
                        },

                        style_header={
                            "fontWeight": "bold",
                            "backgroundColor": "#f2f2f2",
                            "border": "1px solid #d9d9d9",
                            "fontSize": "9px",
                            "padding": "1px 2px",
                            "fontFamily": "monospace",
                            "lineHeight":"14px"
                        },
                        

                        style_data={
                            "border": "1px solid #e5e5e5",
                            "fontSize": "9px",
                            "padding": "0px",
                            "lineHeight": "10px",
                            "height": "10px"
                        }
                    )
                ],
                md=12,
                style={
                    "height": "24vh",
                    "padding": "0",
                    "marginTop": "0.3vh"
                })
            ], className="g-0")
        ], md=6, style={"padding": "0"})
    ], className="g-0")

], fluid=True, style={"height": "100vh", "backgroundColor": "white"})


@app.callback(
    Output("kpi_ca", "figure"),
    Output("kpi_ventes", "figure"),
    Output("graph_CA", "figure"),
    Output("top10ventes", "figure"),
    Output("table_ventes", "data"),
    Input("filtre_location", "value")
)
def update_graphs(locations):
    if locations:
        data_filtre = df[df["Location"].isin(locations)]
    else:
        data_filtre = df

    fig_kpi_ca = plot_chiffre_affaire_mois(data_filtre, 12)
    fig_kpi_ventes = plot_vente_mois(data_filtre, 12, False)
    fig_ca = plot_evolution_chiffre_affaire(data_filtre)
    fig_top10 = barplot_top_10_ventes(data_filtre)

    df_last_100_filtre = data_filtre.sort_values(
        by="Transaction_Date",
        ascending=False
    ).head(100)

    df_last_100_filtre["Transaction_Date"] = pd.to_datetime(
        df_last_100_filtre["Transaction_Date"]
    ).dt.strftime("%d/%m/%Y")

    return (
        fig_kpi_ca,
        fig_kpi_ventes,
        fig_ca,
        fig_top10,
        df_last_100_filtre.to_dict("records")
    )

if __name__ == '__main__':
    app.run(debug=False, port=8063, jupyter_mode="external")
