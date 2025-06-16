import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv


if 'df_commune' in globals() and df_commune is not None and len(df_commune) > 1:
    # Déjà chargé, rien à faire
    pass
else:
    df_commune = pd.read_csv('communes-france-2025.csv')
    
    
# Renommer plusieurs colonnes
df_commune = df_commune.rename(columns={'nom_standard': 'LIBELLE', 'code_insee': 'COM', 'dep_nom': 'DEP'})
print("Données des communes OK")





# Fonction pour filtrer
def filtrer_par_nom(debut, df_commune):
    mask = df_commune['LIBELLE'].str.upper().str.startswith(debut.upper())
    return df_commune[mask]

# Boucle jusqu'à obtenir une sélection
while True:
    debut = input("Entrez le début du nom de la commune : ")
    resultat = filtrer_par_nom(debut, df_commune)
    n = len(resultat)
    if n == 0:
        print("Aucune commune trouvée, recommencez.")
        continue
    elif n == 1:
        choix = 1
    else:
        print("\nVilles trouvées :")
        for i, ville in enumerate(resultat['LIBELLE']):
            print(f"{i+1}. {ville}")
        choix = -1
        while choix < 1 or choix > n:
            try:
                choix = int(input("Votre choix : "))
            except ValueError:
                choix = -1
                
    #☻Enregistrement des variables définitives
    
    ville_choisie = resultat.iloc[choix-1]
    commune = ville_choisie['LIBELLE']
    code_commune = ville_choisie['COM']
    lat_com = ville_choisie['latitude_mairie']
    long_com = ville_choisie['longitude_mairie']
    reg = ville_choisie['reg_nom']
    
    
    
    
    print(f"\nCommune sélectionnée : {ville_choisie['LIBELLE']}")
    print(f"Code INSEE : {ville_choisie['COM']}")
    print(f"Département  : {ville_choisie['DEP']}")
    print(f"lat_com  : {ville_choisie['latitude_mairie']}")
    print(f"long_com  : {ville_choisie['longitude_mairie']}")
    print()
    
    
    break



#Appel du programme "infos_commune"
exec(open('infos_commune_api.py',"r", encoding="utf-8").read())


#Appel du programme pour récupérer les courses
exec(open('courses_commune_api.py',"r", encoding="utf-8").read())

