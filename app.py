# ============================================================
# app.py — Dashboard Dash pour l'analyse des banques sénégalaises
# ============================================================

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import base64

# ============================================================
# CONNEXION MONGODB
# ============================================================
MONGO_URI = "mongodb+srv://ndeyecoumbasamb_db_user:Mong0D3@cluster0.syxao95.mongodb.net/"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["banques_senegal"]

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================
df_excel = pd.DataFrame(list(db["donnees_excel"].find({}, {'_id': 0})))
df_pdf = pd.DataFrame(list(db["donnees_pdf"].find({}, {'_id': 0})))
df = pd.concat([df_excel, df_pdf], ignore_index=True)

df['ANNEE'] = df['ANNEE'].astype(int)
for col in ['PRODUIT.NET.BANCAIRE', 'RESULTAT.NET', 'BILAN', 'EMPLOI',
            'FONDS.PROPRE', 'RESSOURCES', 'EFFECTIF', 'AGENCE', 'COMPTE']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Calcul des ratios financiers
df['ROA'] = (df['RESULTAT.NET'] / df['BILAN'] * 100).round(2)
df['RATIO.SOLVABILITE'] = (df['FONDS.PROPRE'] / df['BILAN'] * 100).round(2)
df['RATIO.LIQUIDITE'] = (df['EMPLOI'] / df['RESSOURCES'] * 100).round(2)

annees = sorted(df['ANNEE'].unique())
banques = sorted(df['Sigle'].unique())

# ============================================================
# INITIALISATION DASH
# ============================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# ============================================================
# MISE EN PAGE
# ============================================================
app.layout = dbc.Container([

    # Titre
    dbc.Row([
        dbc.Col(html.H1("🏦 Analyse des Banques au Sénégal",
                        className="text-center text-warning my-4"))
    ]),

    # Filtres
    dbc.Row([
        dbc.Col([
            html.Label("Filtrer par année :", className="text-white"),
            dcc.Dropdown(
                id='filtre-annee',
                options=[{'label': 'Toutes', 'value': 'Toutes'}] +
                        [{'label': str(a), 'value': a} for a in annees],
                value='Toutes', clearable=False, style={'color': 'black'}
            )
        ], width=4),
        dbc.Col([
            html.Label("Filtrer par banque :", className="text-white"),
            dcc.Dropdown(
                id='filtre-banque',
                options=[{'label': 'Toutes', 'value': 'Toutes'}] +
                        [{'label': b, 'value': b} for b in banques],
                value='Toutes', clearable=False, style={'color': 'black'}
            )
        ], width=4),
        # Bouton téléchargement PDF
        dbc.Col([
            html.Label("Rapport PDF :", className="text-white"),
            html.Br(),
            dbc.Button("📥 Télécharger le rapport", id="btn-pdf",
                       color="warning", className="mt-1"),
            dcc.Download(id="download-pdf")
        ], width=4),
    ], className="mb-4"),

    # Onglets
    dbc.Tabs([

        # ── ONGLET 1 : KPIs Principaux ──
        dbc.Tab(label="📊 KPIs Principaux", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Produit Net Bancaire moyen", className="text-warning mt-3"),
                    dcc.Graph(id='graph-pnb')
                ], width=6),
                dbc.Col([
                    html.H5("Évolution du PNB dans le temps", className="text-warning mt-3"),
                    dcc.Graph(id='graph-evolution-pnb')
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Résultat Net moyen", className="text-warning mt-3"),
                    dcc.Graph(id='graph-resultat')
                ], width=6),
                dbc.Col([
                    html.H5("Comparaison PNB vs Résultat Net — Top 10", className="text-warning mt-3"),
                    dcc.Graph(id='graph-comparaison')
                ], width=6),
            ]),
        ]),

        # ── ONGLET 2 : Bilan & Ressources ──
        dbc.Tab(label="🏛️ Bilan & Ressources", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Bilan par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-bilan')
                ], width=6),
                dbc.Col([
                    html.H5("Évolution du Bilan", className="text-warning mt-3"),
                    dcc.Graph(id='graph-evolution-bilan')
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Ressources par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-ressources')
                ], width=6),
                dbc.Col([
                    html.H5("Fonds Propres par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-fonds-propres')
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Emplois par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-emploi')
                ], width=12),
            ]),
        ]),

        # ── ONGLET 3 : Ratios Financiers ──
        dbc.Tab(label="📈 Ratios Financiers", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("ROA — Rentabilité des Actifs (%)", className="text-warning mt-3"),
                    dcc.Graph(id='graph-roa')
                ], width=6),
                dbc.Col([
                    html.H5("Évolution du ROA", className="text-warning mt-3"),
                    dcc.Graph(id='graph-evolution-roa')
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Ratio de Solvabilité (%)", className="text-warning mt-3"),
                    dcc.Graph(id='graph-solvabilite')
                ], width=6),
                dbc.Col([
                    html.H5("Ratio de Liquidité (%)", className="text-warning mt-3"),
                    dcc.Graph(id='graph-liquidite')
                ], width=6),
            ]),
        ]),

        # ── ONGLET 4 : Réseau & Effectifs ──
        dbc.Tab(label="🏢 Réseau & Effectifs", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Effectifs par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-effectif')
                ], width=6),
                dbc.Col([
                    html.H5("Nombre d'agences par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-agences')
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Évolution des effectifs", className="text-warning mt-3"),
                    dcc.Graph(id='graph-evolution-effectif')
                ], width=6),
                dbc.Col([
                    html.H5("Comptes clients par banque", className="text-warning mt-3"),
                    dcc.Graph(id='graph-comptes')
                ], width=6),
            ]),
        ]),

    ]),

], fluid=True)

# ============================================================
# CALLBACKS — Mise à jour des graphiques
# ============================================================
@app.callback(
    Output('graph-pnb', 'figure'),
    Output('graph-evolution-pnb', 'figure'),
    Output('graph-resultat', 'figure'),
    Output('graph-comparaison', 'figure'),
    Output('graph-bilan', 'figure'),
    Output('graph-evolution-bilan', 'figure'),
    Output('graph-ressources', 'figure'),
    Output('graph-fonds-propres', 'figure'),
    Output('graph-emploi', 'figure'),
    Output('graph-roa', 'figure'),
    Output('graph-evolution-roa', 'figure'),
    Output('graph-solvabilite', 'figure'),
    Output('graph-liquidite', 'figure'),
    Output('graph-effectif', 'figure'),
    Output('graph-agences', 'figure'),
    Output('graph-evolution-effectif', 'figure'),
    Output('graph-comptes', 'figure'),
    Input('filtre-annee', 'value'),
    Input('filtre-banque', 'value')
)
def update_graphs(annee, banque):
    # Application des filtres
    dff = df.copy()
    if annee != 'Toutes':
        dff = dff[dff['ANNEE'] == annee]
    if banque != 'Toutes':
        dff = dff[dff['Sigle'] == banque]

    def bar_h(col, title):
        # Barres horizontales — classement des banques
        d = dff.dropna(subset=[col])
        d = d.groupby('Sigle')[col].mean().reset_index().sort_values(col, ascending=True)
        return px.bar(d, x=col, y='Sigle', orientation='h',
                      title=title, color=col,
                      color_continuous_scale='Viridis', template='plotly_dark')

    def pie_chart(col, title):
        # Camembert — répartition entre banques
        d = dff.dropna(subset=[col])
        d = d.groupby('Sigle')[col].mean().reset_index()
        d = d[d[col] > 0]
        return px.pie(d, values=col, names='Sigle', title=title,
                      template='plotly_dark', hole=0.3)

    def scatter_chart(col_x, col_y, title):
        # Nuage de points — corrélation entre deux indicateurs
        d = dff.dropna(subset=[col_x, col_y])
        return px.scatter(d, x=col_x, y=col_y, color='Sigle',
                          size=col_x, hover_name='Sigle',
                          title=title, template='plotly_dark')

    def line_evol(col, title):
        # Courbes d'évolution temporelle
        d = df.copy()
        if banque != 'Toutes':
            d = d[d['Sigle'] == banque]
        d = d.dropna(subset=[col])
        d = d.groupby(['ANNEE', 'Sigle'])[col].mean().reset_index()
        return px.line(d, x='ANNEE', y=col, color='Sigle',
                       title=title, markers=True, template='plotly_dark')

    def bar_group(col, title):
        # Barres groupées par année
        d = dff.dropna(subset=[col])
        d = d.groupby(['Sigle', 'ANNEE'])[col].mean().reset_index()
        return px.bar(d, x='Sigle', y=col, color='ANNEE',
                      barmode='group', title=title, template='plotly_dark')

    # Comparaison PNB vs Résultat Net — Top 10
    d_comp = dff.dropna(subset=['PRODUIT.NET.BANCAIRE', 'RESULTAT.NET'])
    d_comp = d_comp.groupby('Sigle')[['PRODUIT.NET.BANCAIRE', 'RESULTAT.NET']].mean().reset_index()
    d_comp = d_comp.nlargest(10, 'PRODUIT.NET.BANCAIRE')
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='PNB', x=d_comp['Sigle'],
                               y=d_comp['PRODUIT.NET.BANCAIRE'], marker_color='#f0a500'))
    fig_comp.add_trace(go.Bar(name='Résultat Net', x=d_comp['Sigle'],
                               y=d_comp['RESULTAT.NET'], marker_color='#00bc8c'))
    fig_comp.update_layout(barmode='group', template='plotly_dark',
                            title='Top 10 — PNB vs Résultat Net (Millions FCFA)')

    return (
        bar_h('PRODUIT.NET.BANCAIRE', 'PNB moyen (Millions FCFA)'),
        line_evol('PRODUIT.NET.BANCAIRE', 'Évolution du PNB'),
        bar_h('RESULTAT.NET', 'Résultat Net moyen (Millions FCFA)'),
        fig_comp,
        bar_h('BILAN', 'Bilan moyen (Millions FCFA)'),
        line_evol('BILAN', 'Évolution du Bilan'),
        pie_chart('RESSOURCES', 'Répartition des Ressources'),
        bar_h('FONDS.PROPRE', 'Fonds Propres moyens (Millions FCFA)'),
        scatter_chart('EMPLOI', 'BILAN', 'Emplois vs Bilan'),
        bar_h('ROA', 'ROA moyen (%)'),
        line_evol('ROA', 'Évolution du ROA'),
        bar_h('RATIO.SOLVABILITE', 'Ratio Solvabilité moyen (%)'),
        bar_h('RATIO.LIQUIDITE', 'Ratio Liquidité moyen (%)'),
        bar_h('EFFECTIF', 'Effectif moyen'),
        pie_chart('AGENCE', 'Répartition des agences'),
        line_evol('EFFECTIF', 'Évolution des effectifs'),
        bar_group('COMPTE', 'Comptes clients par banque et par année'),
    )

# ============================================================
# CALLBACK — Téléchargement PDF
# ============================================================
@app.callback(
    Output("download-pdf", "data"),
    Input("btn-pdf", "n_clicks"),
    Input('filtre-banque', 'value'),
    Input('filtre-annee', 'value'),
    prevent_initial_call=True
)
def telecharger_pdf(n_clicks, banque, annee):
    if not n_clicks:
        return None

    # Filtrage des données pour le rapport
    dff = df.copy()
    if annee != 'Toutes':
        dff = dff[dff['ANNEE'] == annee]
    if banque != 'Toutes':
        dff = dff[dff['Sigle'] == banque]

    # Calcul des moyennes pour le rapport
    pnb_moy = dff['PRODUIT.NET.BANCAIRE'].mean()
    net_moy = dff['RESULTAT.NET'].mean()
    bilan_moy = dff['BILAN'].mean() if 'BILAN' in dff.columns else None
    roa_moy = dff['ROA'].mean()

    # Génération du PDF en mémoire
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Titre
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 60, "Rapport de Positionnement Bancaire")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 85, f"Banque : {banque if banque != 'Toutes' else 'Toutes les banques'}")
    c.drawString(50, height - 105, f"Année  : {annee if annee != 'Toutes' else 'Toutes les années'}")

    # Ligne séparatrice
    c.line(50, height - 120, width - 50, height - 120)

    # KPIs
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 150, "Indicateurs Clés :")
    c.setFont("Helvetica", 12)
    y = height - 175
    kpis = [
        ("Produit Net Bancaire moyen", pnb_moy, "Millions FCFA"),
        ("Résultat Net moyen", net_moy, "Millions FCFA"),
        ("Bilan moyen", bilan_moy, "Millions FCFA"),
        ("ROA moyen", roa_moy, "%"),
    ]
    for label, valeur, unite in kpis:
        val_str = f"{valeur:,.0f} {unite}" if pd.notna(valeur) else "N/D"
        c.drawString(60, y, f"• {label} : {val_str}")
        y -= 25

    # Note de bas de page
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 40, "Source : BCEAO — Base Sénégal Bancaire | Généré automatiquement")

    c.save()
    buffer.seek(0)

    # Encodage base64 pour le téléchargement
    pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    nom_fichier = f"rapport_{banque}_{annee}.pdf"

    return dict(content=pdf_base64, filename=nom_fichier, base64=True, type="application/pdf")

# ============================================================
# LANCEMENT
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)
