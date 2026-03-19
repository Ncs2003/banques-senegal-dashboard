# ============================================================
# test_data.py — Tests unitaires pour vérifier l'intégrité des données
# ============================================================

import pandas as pd
from pymongo import MongoClient

# ============================================================
# CONNEXION MONGODB
# ============================================================
MONGO_URI = "mongodb+srv://ndeyecoumbasamb_db_user:Mong0D3@cluster0.syxao95.mongodb.net/"
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client["banques_senegal"]

# Chargement des données
df_excel = pd.DataFrame(list(db["donnees_excel"].find({}, {'_id': 0})))
df_pdf = pd.DataFrame(list(db["donnees_pdf"].find({}, {'_id': 0})))
df = pd.concat([df_excel, df_pdf], ignore_index=True)

for col in ['PRODUIT.NET.BANCAIRE', 'RESULTAT.NET', 'BILAN', 'EMPLOI',
            'FONDS.PROPRE', 'RESSOURCES', 'EFFECTIF', 'AGENCE', 'COMPTE']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# ============================================================
# TESTS
# ============================================================

def test_donnees_non_vides():
    # Vérifie que les collections ne sont pas vides
    assert len(df) > 0, "❌ Le DataFrame est vide !"
    print("✅ Test 1 — Données non vides : OK")

def test_colonnes_obligatoires():
    # Vérifie que les colonnes essentielles existent
    colonnes = ['Sigle', 'ANNEE', 'PRODUIT.NET.BANCAIRE', 'RESULTAT.NET']
    for col in colonnes:
        assert col in df.columns, f"❌ Colonne manquante : {col}"
    print("✅ Test 2 — Colonnes obligatoires présentes : OK")

def test_annees_valides():
    # Vérifie que les années sont dans la plage attendue
    assert df['ANNEE'].min() >= 2015, "❌ Année trop ancienne détectée"
    assert df['ANNEE'].max() <= 2022, "❌ Année trop récente détectée"
    print("✅ Test 3 — Années valides (2015-2022) : OK")

def test_sigles_non_nuls():
    # Vérifie qu'aucun sigle n'est vide
    assert df['Sigle'].isnull().sum() == 0, "❌ Des sigles sont manquants !"
    print("✅ Test 4 — Sigles non nuls : OK")

def test_pnb_numerique():
    # Vérifie que le PNB est bien numérique
    assert df['PRODUIT.NET.BANCAIRE'].dtype in ['float64', 'int64'], \
        "❌ PNB n'est pas numérique !"
    print("✅ Test 5 — PNB numérique : OK")

def test_nombre_banques():
    # Vérifie qu'on a au moins 20 banques distinctes
    nb_banques = df['Sigle'].nunique()
    assert nb_banques >= 20, f"❌ Seulement {nb_banques} banques détectées !"
    print(f"✅ Test 6 — Nombre de banques ({nb_banques}) : OK")

def test_excel_et_pdf():
    # Vérifie que les deux sources sont bien chargées
    assert len(df_excel) > 0, "❌ Données Excel vides !"
    assert len(df_pdf) > 0, "❌ Données PDF vides !"
    print(f"✅ Test 7 — Excel ({len(df_excel)} lignes) + PDF ({len(df_pdf)} lignes) : OK")

# ============================================================
# LANCEMENT DES TESTS
# ============================================================
if __name__ == '__main__':
    print("\n🔍 Lancement des tests unitaires...\n")
    test_donnees_non_vides()
    test_colonnes_obligatoires()
    test_annees_valides()
    test_sigles_non_nuls()
    test_pnb_numerique()
    test_nombre_banques()
    test_excel_et_pdf()
    print("\n✅ Tous les tests sont passés avec succès !")
