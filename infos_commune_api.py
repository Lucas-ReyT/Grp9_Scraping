
###### DEBUT DU SCRAPPING
lien_scrapping = "https://www.bien-dans-ma-ville.fr/"+str(commune.lower())+"-"+str(code_commune)



# Requête HTTP pour récupérer le contenu
reponse = requests.get(lien_scrapping)
html = reponse.text

# Création de l'objet BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')



# Ouvrir (ou créer) le fichier et écrire la variable dedans
with open('scrap.html', 'w', encoding='utf-8') as fichier:
    fichier.write(str(soup))




# Extraction des infos principales
def extract_infos(soup):
    data = {}
    
    # Informations générales
    try:
        title = soup.find('title').text.strip()
        data['titre'] = title
    except:
        data['titre'] = ''
    
    # Population et statistiques démographiques
    try:
        # Recherche dans les tableaux de statistiques
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # Mapping des clés importantes
                    if 'Population' in key or 'Habitants' in key:
                        data['population'] = value
                    elif 'Superficie' in key:
                        data['superficie'] = value
                    elif 'Densité' in key or 'Pop densité' in key:
                        data['densite'] = value
                    elif 'Revenu' in key:
                        data['revenu_moyen'] = value
                    elif 'Chômage' in key or 'chômage' in key:
                        data['taux_chomage'] = value
                    elif 'Prix immobilier' in key:
                        data['prix_immobilier'] = value
    except:
        pass
    
    # Informations depuis les méta-données
    try:
        description = soup.find('meta', {'name': 'description'})
        if description:
            data['description'] = description.get('content', '')
    except:
        data['description'] = ''
    
    # Sécurité - Chiffres de délinquance
    try:
        securite_section = soup.find('section', {'id': 'securite'})
        if securite_section:
            securite_table = securite_section.find('table', class_='bloc_chiffre')
            if securite_table:
                rows = securite_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        crime_type = cells[0].get_text(strip=True)
                        crime_count = cells[1].get_text(strip=True)
                        
                        if 'Agressions' in crime_type:
                            data['agressions'] = crime_count
                        elif 'Cambriolages' in crime_type:
                            data['cambriolages'] = crime_count
                        elif 'Vols' in crime_type:
                            data['vols_degradations'] = crime_count
                        elif 'Stupéfiants' in crime_type:
                            data['stupefiants'] = crime_count
    except:
        pass
    
    # Services et équipements - Santé
    try:
        service_divs = soup.find_all('div', class_='service')
        for service_div in service_divs:
            table = service_div.find('table')
            if table:
                header = table.find('h3')
                if header and 'Santé' in header.text:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            service_type = cells[0].get_text(strip=True)
                            service_count = cells[1].get_text(strip=True)
                            
                            # Nettoyer le nom du service pour en faire une clé
                            service_key = service_type.lower().replace(' ', '_').replace('-', '_')
                            data[f'sante_{service_key}'] = service_count
                
                elif header and 'Éducation' in header.text:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            service_type = cells[0].get_text(strip=True)
                            service_count = cells[1].get_text(strip=True)
                            
                            service_key = service_type.lower().replace(' ', '_').replace('-', '_')
                            data[f'education_{service_key}'] = service_count
    except:
        pass
    
    # Résultats électoraux (Présidentielles)
    try:
        tour1_section = soup.find('div', class_='tour1')
        if tour1_section:
            candidats = tour1_section.find_all('div', class_='candidat')
            for i, candidat in enumerate(candidats):
                nom_elem = candidat.find('div', class_='nom')
                score_elem = candidat.find('div', class_='score')
                
                if nom_elem and score_elem:
                    nom = nom_elem.find('span').text.strip() if nom_elem.find('span') else ''
                    score = score_elem.text.strip()
                    data[f'presidentielles_tour1_{i+1}_nom'] = nom
                    data[f'presidentielles_tour1_{i+1}_score'] = score
        
        # Participation Tour 1
        total_div = tour1_section.find('div', class_='total') if tour1_section else None
        if total_div:
            total_text = total_div.get_text()
            if 'Participation' in total_text:
                lines = total_text.split('\n')
                for line in lines:
                    if 'Participation' in line:
                        data['participation_tour1'] = line.split(':')[1].strip() if ':' in line else ''
        
        # Tour 2
        tour2_section = soup.find('div', class_='tour2')
        if tour2_section:
            candidats_t2 = tour2_section.find_all('div', class_='candidat')
            for i, candidat in enumerate(candidats_t2):
                nom_elem = candidat.find('div', class_='nom')
                score_elem = candidat.find('div', class_='score')
                
                if nom_elem and score_elem:
                    nom = nom_elem.find('span').text.strip() if nom_elem.find('span') else ''
                    score = score_elem.text.strip()
                    data[f'presidentielles_tour2_{i+1}_nom'] = nom
                    data[f'presidentielles_tour2_{i+1}_score'] = score
    except:
        pass
    
    # Villes voisines (tableau comparatif)
    try:
        villes_voisines = []
        tbody = soup.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows[:5]:  # Limiter aux 5 premières villes
                cells = row.find_all('td')
                if len(cells) > 0:
                    ville_link = cells[0].find('a')
                    if ville_link:
                        ville_nom = ville_link.text.replace('Statistiques ', '').strip()
                        villes_voisines.append(ville_nom)
        
        data['villes_voisines'] = ', '.join(villes_voisines)
    except:
        data['villes_voisines'] = ''
    
    # Note globale (si disponible)
    try:
        note_elements = soup.find_all('td', class_='actif')
        # Chercher une note globale dans les tableaux
        for element in note_elements:
            if element.get_text(strip=True).replace('.', '').isdigit():
                # Logique pour identifier la note globale
                pass
    except:
        pass
    
    # Informations bonus depuis les balises "Bon à savoir"
    try:
        infos_divs = soup.find_all('div', class_='infos')
        bon_a_savoir = []
        for info_div in infos_divs:
            ul = info_div.find('ul')
            if ul:
                lis = ul.find_all('li')
                for li in lis:
                    bon_a_savoir.append(li.get_text(strip=True))
        
        data['bon_a_savoir'] = ' | '.join(bon_a_savoir)
    except:
        data['bon_a_savoir'] = ''
    
    # URL de l'image de la ville
    try:
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image:
            data['image_url'] = og_image.get('content', '')
    except:
        data['image_url'] = ''
    
    return data


# Récupère les infos
infos = extract_infos(soup)

    
import json
# Exportation vers un fichier JSON
with open("info_commune.json", "w", encoding="utf-8") as fichier:
    json.dump(infos, fichier, ensure_ascii=False, indent=4)
    
print("Infos commune OK - Fichier JSON généré")