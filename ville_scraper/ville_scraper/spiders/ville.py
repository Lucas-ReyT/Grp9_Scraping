import scrapy
import re

class JobijobaSpider(scrapy.Spider):
    name = "jobijoba"

    def __init__(self, ville=None, contract_type=None, what=None, salaire_min=None, *args, **kwargs):
        super(JobijobaSpider, self).__init__(*args, **kwargs)
        self.ville = ville
        self.contract_type = contract_type
        self.what = what
        self.salaire_min = int(salaire_min) if salaire_min else None

    def start_requests(self):
        url = (
            f"https://www.jobijoba.com/fr/query/?where={self.ville}"
            f"&where_type=city&contract_type={self.contract_type}"
            f"&what={self.what}"
        )
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        offres = response.css("div.offer")
        idx = 0

        for offre in offres:
            titre = offre.css("h3.offer-header-title::text").get()
            lien = offre.css("a.offer-link::attr(href)").get()
            salaire_raw = offre.css("div.offer-features div.feature::text").getall()
            salaire_texte = " ".join(salaire_raw).strip()

            
            if self.what and (not titre or self.what.lower() not in titre.lower()):
                continue

            
            salaire_valide = self.extract_salaire(salaire_texte)

            
            if salaire_valide is None or (self.salaire_min and salaire_valide < self.salaire_min):
                continue

            idx += 1

            yield {
                "ville": self.ville,
                "contract_type": self.contract_type,
                "what": self.what,
                "offre_n": idx,
                "titre_offre": titre.strip(),
                "salaire": salaire_texte,
                "url": response.urljoin(lien),
            }

    def extract_salaire(self, texte):
        
        texte = texte.replace("\u202f", " ").replace("\xa0", " ")

        
        match = re.search(r"De\s*(\d[\d\s]*)\s*€", texte)
        if match:
            montant = match.group(1).replace(" ", "").replace(".", "")
            try:
                return int(montant)
            except ValueError:
                return None

        
        match2 = re.search(r"(\d[\d\s]*)\s*€", texte)
        if match2:
            montant = match2.group(1).replace(" ", "").replace(".", "")
            try:
                return int(montant)
            except ValueError:
                return None

        return None
