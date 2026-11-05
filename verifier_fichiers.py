
import sqlite3

connexion = sqlite3.connect("arctic.db")

curseur = connexion.cursor()

curseur.execute("""
    SELECT
        oeuvre.id,
        oeuvre.titre,
        oeuvre.type,
        fichier_oeuvre.type_fichier,
        fichier_oeuvre.chemin_fichier
    FROM oeuvre
    LEFT JOIN fichier_oeuvre
        ON oeuvre.id = fichier_oeuvre.oeuvre_id
    ORDER BY oeuvre.id DESC
    LIMIT 10
""")

resultats = curseur.fetchall()

for ligne in resultats:
    print(ligne)

connexion.close()
