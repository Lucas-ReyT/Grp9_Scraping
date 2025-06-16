import requests
from bs4 import BeautifulSoup
import json
import re
import html

###### DEBUT DU SCRAPPING
lien_scrapping = "https://running.life/calendrier-course-a-pied/france/"+str(reg.lower())+"/"+str(commune.lower())

# Requête HTTP pour récupérer le contenu
reponse = requests.get(lien_scrapping)
html_content = reponse.text

# Création de l'objet BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Ouvrir (ou créer) le fichier et écrire la variable dedans
with open('scrap_courses.html', 'w', encoding='utf-8') as fichier:
    fichier.write(str(html_content))

# Extraction des infos principales
def extract_infos(soup):
    data = {
        "courses": [],
        "meta_info": {},
        "location_info": {},
        "livewire_data": {},
        "map_config": {}
    }
    
    try:
        # 1. Extraction des métadonnées de la page
        title = soup.find('title')
        if title:
            data["meta_info"]["title"] = title.get_text().strip()
            
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            data["meta_info"]["description"] = description.get('content', '')
        
        # URL canonique
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            data["meta_info"]["canonical_url"] = canonical.get('href', '')
        
        # 2. Fonction pour extraire les distances d'une course depuis le HTML
        def extract_course_distances_from_html(course_url):
            distances = []
            # Chercher tous les liens qui pointent vers cette course avec des distances
            course_links = soup.find_all('a', href=course_url)
            for link in course_links:
                link_text = link.get_text().strip()
                # Recherche de patterns comme "11 km", "17 km", etc.
                distance_match = re.search(r'(\d+(?:\.\d+)?)\s*km', link_text, re.I)
                if distance_match:
                    distance = distance_match.group(1)
                    if distance not in distances:
                        distances.append(distance)
            return distances
        
        def extract_course_type_from_html(course_url):
            course_type = ""
            # Chercher tous les liens qui pointent vers cette course pour trouver le type
            course_links = soup.find_all('a', href=course_url)
            for link in course_links:
                # Chercher dans les classes CSS pour identifier le type
                classes = link.get('class', [])
                link_text = link.get_text().strip().lower()
                
                # Identification du type selon les classes CSS ou le texte
                if 'bg-green-200' in classes or 'trail' in link_text:
                    course_type = "Trail"
                elif 'bg-blue-200' in classes or 'route' in link_text or 'course' in link_text:
                    course_type = "Course sur route"
                elif 'bg-orange-200' in classes or 'marche' in link_text:
                    course_type = "Marche"
                else:
                    # Si on trouve un type dans le texte, on le prend
                    if link_text in ['trail', 'course', 'marathon', 'semi', '10k', '5k']:
                        course_type = link_text.title()
                
                if course_type:
                    break
            
            return course_type if course_type else "Course à pied"

        # 3. Extraction des événements depuis les scripts JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.get_text())
                if json_data.get('@type') == 'Event':
                    course_url = json_data.get('url', '')
                    
                    course = {
                        "name": json_data.get('name', ''),
                        "start_date": json_data.get('startDate', ''),
                        "end_date": json_data.get('endDate', ''),
                        "url": course_url,
                        "event_status": json_data.get('eventStatus', ''),
                        "distances": extract_course_distances_from_html(course_url),
                        "type": extract_course_type_from_html(course_url),
                        "location": {}
                    }
                    
                    # Extraction des informations de lieu
                    if 'location' in json_data:
                        location = json_data['location']
                        course["location"] = {
                            "name": location.get('name', ''),
                            "address": {
                                "country": location.get('address', {}).get('addressCountry', ''),
                                "locality": location.get('address', {}).get('addressLocality', ''),
                                "region": location.get('address', {}).get('addressRegion', '')
                            },
                            "coordinates": {
                                "latitude": location.get('geo', {}).get('latitude', ''),
                                "longitude": location.get('geo', {}).get('longitude', '')
                            }
                        }
                    
                    # Calcul de la distance depuis Carcassonne si disponible
                    # Chercher dans le HTML les informations de distance
                    distance_info = ""
                    sections = soup.find_all('section')
                    for section in sections:
                        if course['name'] in section.get_text():
                            distance_spans = section.find_all('span', string=re.compile(r'\d+\s*km de'))
                            for span in distance_spans:
                                distance_text = span.get_text()
                                distance_match = re.search(r'(\d+)\s*km de ([^|]+)', distance_text)
                                if distance_match:
                                    distance_info = f"{distance_match.group(1)} km de {distance_match.group(2).strip()}"
                                    break
                    
                    course["distance_from_center"] = distance_info
                    
                    data["courses"].append(course)
                    
            except json.JSONDecodeError:
                continue
        
        # 4. Amélioration : extraction des courses depuis le HTML visible si les JSON-LD ne suffisent pas
        # Chercher les sections qui contiennent des courses
        course_sections = soup.find_all('section')
        for section in course_sections:
            # Chercher les titres de courses (h2)
            course_title = section.find('h2')
            if course_title:
                course_name = course_title.get_text().strip()
                course_link = section.find('a', href=True)
                
                # Vérifier si cette course n'est pas déjà dans notre liste
                already_exists = any(c['name'] == course_name for c in data["courses"])
                if not already_exists and course_link:
                    course_url = course_link.get('href', '')
                    
                    # Extraire les distances directement de cette section
                    distances = []
                    distance_links = section.find_all('a', string=re.compile(r'\d+\s*km'))
                    for dist_link in distance_links:
                        dist_text = dist_link.get_text().strip()
                        dist_match = re.search(r'(\d+(?:\.\d+)?)\s*km', dist_text)
                        if dist_match:
                            distances.append(dist_match.group(1))
                    
                    # Extraire le type de course
                    course_type = "Course à pied"
                    type_links = section.find_all('a', class_=re.compile(r'bg-\w+-200'))
                    for type_link in type_links:
                        type_text = type_link.get_text().strip().lower()
                        if 'trail' in type_text:
                            course_type = "Trail"
                        elif 'route' in type_text:
                            course_type = "Course sur route"
                    
                    # Extraire la date depuis le calendrier visible
                    date_info = {}
                    date_div = section.find('div', class_=re.compile(r'rounded-xl.*bg-white'))
                    if date_div:
                        month_div = date_div.find('div', class_=re.compile(r'bg-red-700'))
                        day_div = date_div.find('div', class_=re.compile(r'text-\[23px\]'))
                        weekday_div = date_div.find('div', class_=re.compile(r'text-\[10px\]'))
                        
                        if month_div and day_div:
                            month = month_div.get_text().strip()
                            day = day_div.get_text().strip()
                            weekday = weekday_div.get_text().strip() if weekday_div else ""
                            
                            # Conversion du mois français en numéro
                            month_mapping = {
                                'jan': '01', 'fév': '02', 'mar': '03', 'avr': '04',
                                'mai': '05', 'juin': '06', 'juil': '07', 'août': '08',
                                'sept': '09', 'oct': '10', 'nov': '11', 'déc': '12'
                            }
                            month_num = month_mapping.get(month.lower(), '01')
                            
                            # Construire la date (année par défaut 2025)
                            date_info = {
                                "formatted_date": f"2025-{month_num}-{day.zfill(2)}",
                                "month": month,
                                "day": day,
                                "weekday": weekday
                            }
                    
                    course = {
                        "name": course_name,
                        "url": course_url,
                        "distances": distances,
                        "type": course_type,
                        "date_info": date_info,
                        "start_date": date_info.get("formatted_date", ""),
                        "end_date": date_info.get("formatted_date", ""),
                        "location": {
                            "name": "",
                            "address": {},
                            "coordinates": {}
                        },
                        "distance_from_center": ""
                    }
                    
                    data["courses"].append(course)
        
        # 5. Extraction des données Livewire
        livewire_div = soup.find('div', attrs={'wire:snapshot': True})
        if livewire_div:
            wire_snapshot = livewire_div.get('wire:snapshot', '')
            try:
                wire_snapshot = html.unescape(wire_snapshot)
                livewire_data = json.loads(wire_snapshot)
                
                data["livewire_data"] = {
                    "search_text": livewire_data.get('data', {}).get('searchText', ''),
                    "country_code": livewire_data.get('data', {}).get('countryCode', ''),
                    "distance_from_location": livewire_data.get('data', {}).get('distanceFromLocation', 0),
                    "location_key": livewire_data.get('data', {}).get('location', [None, {}])[1].get('key', ''),
                    "path": livewire_data.get('memo', {}).get('path', ''),
                    "locale": livewire_data.get('memo', {}).get('locale', '')
                }
                
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # 6. Extraction de la configuration de carte
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.get_text()
            
            center_match = re.search(r'center:\s*\[([0-9.-]+),\s*([0-9.-]+)\]', script_text)
            if center_match:
                data["map_config"]["center"] = {
                    "longitude": float(center_match.group(1)),
                    "latitude": float(center_match.group(2))
                }
            
            zoom_match = re.search(r'zoom:\s*(\d+)', script_text)
            if zoom_match:
                data["map_config"]["zoom"] = int(zoom_match.group(1))
        
        # 7. Extraction des liens de langues alternatives
        hreflang_links = soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
        data["meta_info"]["languages"] = {}
        for link in hreflang_links:
            lang = link.get('hreflang')
            href = link.get('href')
            data["meta_info"]["languages"][lang] = href
        
        # 8. Informations générales
        description_text = data["meta_info"].get("description", "")
        course_count_match = re.search(r'(\d+)\s+courses?\s+passionnantes?', description_text)
        if course_count_match:
            data["meta_info"]["total_courses_announced"] = int(course_count_match.group(1))
        
        data["meta_info"]["total_courses_found"] = len(data["courses"])
        data["meta_info"]["scraping_url"] = lien_scrapping
        data["meta_info"]["main_location"] = commune.title()
        
        # Extraction des villes concernées
        cities = set()
        for course in data["courses"]:
            city = course.get("location", {}).get("address", {}).get("locality", "")
            if city:
                cities.add(city)
        data["meta_info"]["cities_involved"] = sorted(list(cities))
        
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        data["error"] = str(e)
    
    return data

# Récupère les infos
infos = extract_infos(soup)


# Exportation vers un fichier JSON
with open("courses_commune.json", "w", encoding="utf-8") as fichier:
    json.dump(infos, fichier, ensure_ascii=False, indent=4)
    
print("Courses commune OK - Fichier JSON généré ")
