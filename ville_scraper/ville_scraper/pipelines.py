# pipelines.py
import re
import json
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class JobiJobaPipeline:
    
    def __init__(self):
        self.seen_urls = set()
        self.items_count = 0
    
    def open_spider(self, spider):
        """Méthode appelée à l'ouverture du spider"""
        spider.logger.info("Pipeline JobiJoba démarré")
    
    def close_spider(self, spider):
        """Méthode appelée à la fermeture du spider"""
        spider.logger.info(f"Pipeline JobiJoba terminé - {self.items_count} items traités")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 1. Vérifier les champs obligatoires
        if not adapter.get('titre_offre') or not adapter.get('url'):
            raise DropItem(f"Item incomplet: {item}")
        
        # 2. Éviter les doublons basés sur l'URL
        if adapter['url'] in self.seen_urls:
            raise DropItem(f"Doublon détecté: {adapter['url']}")
        self.seen_urls.add(adapter['url'])
        
        # 3. Nettoyer et traiter les données
        self._clean_item(adapter)
        
        self.items_count += 1
        return item
    
    def _clean_item(self, adapter):
        """Nettoie et traite les données de l'item"""
        
        # Nettoyer le titre
        if adapter.get('titre_offre'):
            adapter['titre_offre'] = adapter['titre_offre'].strip()
        
        # Traiter le salaire
        if adapter.get('salaire'):
            adapter['salaire_brut'] = adapter['salaire']  # Garder l'original
            adapter['salaire_nettoye'] = self._clean_salaire_text(adapter['salaire'])
            salaire_info = self._extract_salaire_info(adapter['salaire'])
            adapter.update(salaire_info)
    
    def _clean_salaire_text(self, salaire_text):
        """Nettoie le texte du salaire"""
        if not salaire_text:
            return ""
        
        # Remplacer les caractères spéciaux
        cleaned = salaire_text.replace("\u202f", " ").replace("\xa0", " ")
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _extract_salaire_info(self, salaire_text):
        """Extrait les informations détaillées du salaire"""
        if not salaire_text:
            return {
                'salaire_min': None,
                'salaire_max': None,
                'salaire_type': None,
                'devise': None
            }
        
        # Nettoyer le texte
        text = salaire_text.replace("\u202f", " ").replace("\xa0", " ")
        
        # Détecter le type de salaire
        salaire_type = "annuel"  # par défaut
        if "par mois" in text.lower() or "mensuel" in text.lower():
            salaire_type = "mensuel"
        elif "par jour" in text.lower():
            salaire_type = "journalier"
        elif "par heure" in text.lower():
            salaire_type = "horaire"
        
        # Extraire les montants
        salaire_min = None
        salaire_max = None
        devise = "EUR"  # par défaut
        
        # Pattern pour "De X € à Y €"
        pattern_range = r"De\s*(\d[\d\s]*)\s*€\s*à\s*(\d[\d\s]*)\s*€"
        match_range = re.search(pattern_range, text)
        
        if match_range:
            try:
                salaire_min = int(match_range.group(1).replace(" ", ""))
                salaire_max = int(match_range.group(2).replace(" ", ""))
            except ValueError:
                pass
        else:
            # Pattern pour un seul montant
            pattern_single = r"(\d[\d\s]*)\s*€"
            match_single = re.search(pattern_single, text)
            if match_single:
                try:
                    montant = int(match_single.group(1).replace(" ", ""))
                    salaire_min = montant
                    salaire_max = montant
                except ValueError:
                    pass
        
        return {
            'salaire_min': salaire_min,
            'salaire_max': salaire_max,
            'salaire_type': salaire_type,
            'devise': devise
        }


class JsonWriterPipeline:
    """Pipeline pour sauvegarder les données en JSON"""
    
    def __init__(self):
        self.items = []
    
    def open_spider(self, spider):
        pass
    
    def close_spider(self, spider):
        # Sauvegarder tous les items dans un fichier JSON
        filename = f"jobijoba_{spider.ville}_{spider.what}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        spider.logger.info(f"Items sauvegardés dans {filename}")
    
    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item


class StatsPipeline:
    """Pipeline pour collecter des statistiques"""
    
    def __init__(self):
        self.stats = {
            'total_items': 0,
            'salaire_ranges': {},
            'contract_types': {},
        }
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.stats['total_items'] += 1
        
        # Stats par type de contrat
        contract_type = adapter.get('contract_type', 'Unknown')
        self.stats['contract_types'][contract_type] = self.stats['contract_types'].get(contract_type, 0) + 1
        
        # Stats de salaire
        salaire_min = adapter.get('salaire_min')
        if salaire_min:
            if salaire_min < 30000:
                range_key = "< 30k"
            elif salaire_min < 50000:
                range_key = "30k-50k"
            elif salaire_min < 70000:
                range_key = "50k-70k"
            else:
                range_key = "> 70k"
            
            self.stats['salaire_ranges'][range_key] = self.stats['salaire_ranges'].get(range_key, 0) + 1
        
        return item
    
    def close_spider(self, spider):
        # Afficher les statistiques
        spider.logger.info("=== STATISTIQUES ===")
        spider.logger.info(f"Total d'offres: {self.stats['total_items']}")
        spider.logger.info(f"Répartition par salaire: {self.stats['salaire_ranges']}")
        spider.logger.info(f"Répartition par contrat: {self.stats['contract_types']}")
