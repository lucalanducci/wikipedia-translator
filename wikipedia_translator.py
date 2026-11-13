#!/usr/bin/env python3
"""
Wikipedia English to Italian Translator with Claude AI
Maintains Italian Wikipedia conventions and templates
"""

import re
import requests
import os
import json
from typing import Dict, List, Tuple
from anthropic import Anthropic

class WikipediaTranslator:
    """Traduttore di articoli Wikipedia dall'inglese all'italiano"""

    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-opus-5"
        self.rules = {
            "bio_template": {
                "description": "Usa {{Bio}} per le persone in italiano, non {{Infobox persona}}",
                "luogo_nascita_link": "Specifica LuogoNascitaLink solo se diverso da LuogoNascita",
                "post_nazionalita": "Metti la descrizione della persona nel campo PostNazionalità, non in un paragrafo separato",
                "no_incipit_paragraph": "Il template {{Bio}} genera l'incipit automaticamente - NON aggiungere '''Nome''' è..."
            },
            "citazioni": {
                "template": "Usa {{Cita web}} in italiano, non {{cite web}} inglese",
                "parametri": "title→titolo, website→sito, access-date→accesso, date→data, author→autore",
                "link_url": "L'URL deve comprendere il prefisso (http:// o https://)"
            },
            "wikilink_istituzioni": {
                "universita": "Università di [città] non Università [città]",
                "esempio": "[[Università di Stanford]] non [[Università Stanford]]",
                "scuole": "NYU Tisch School of the Arts rimane come è (nome proprio inglese)"
            },
            "wikilink_verifica": {
                "critico": "VERIFICARE SEMPRE che i wikilink esistono in italiano Wikipedia",
                "metodo": "Se il link inglese non esiste in italiano, cercare il corrispettivo italiano e usare quello",
                "esempio_premi": "[[BAFTA Award for Outstanding Debut...]] → [[BAFTA al miglior esordio britannico...]]",
                "esempio_attori": "[[Alessandro Borghi (actor)|...]] → [[Alessandro Borghi]]",
                "nota": "Molti link a premi/festival/attori hanno nomi diversi o disambigua diversa in italiano - rimuovere '(actor)' e simili"
            },
            "categorie": {
                "bio_auto": "Il template {{Bio}} genera automaticamente le categorie",
                "bio_no_manuali": "Per persone ({{Bio}}): NON aggiungere manualmente categorie",
                "film_manuali": "Per film ({{Film}}): le categorie vanno aggiunte MANUALMENTE",
                "verifica_categorie": "VERIFICARE SEMPRE che le categorie esistono in italiano Wikipedia prima di aggiungerle",
                "categoria_film": "Categorie film da verificare: Film italiani del YYYY, Film drammatici, Film diretti da [regista], etc"
            },
            "sezione_note": {
                "intestazione": "== Note ==",
                "template": "Usa <references/> non {{Reflist}}"
            },
            "defaultsort": {
                "regola": "NON aggiungere {{DEFAULTSORT:...}} - viene generato automaticamente da {{Bio}}"
            },
            "sezioni": {
                "biografia": "La sezione iniziale deve essere == Biografia == non == Primi anni ==",
                "carriera": "== Carriera == rimane uguale"
            },
            "post_nazionalita_punto": {
                "regola": "NON mettere il punto alla fine di PostNazionalità - viene aggiunto automaticamente da {{Bio}}"
            },
            "template_film": {
                "template": "Usa {{Film}} per i film, non {{Infobox film}}",
                "parametri_obbligatori": "titolo, paese, anno uscita, genere, regista",
                "parametri_comuni": "titolo originale, lingua originale, durata, attori, doppiatori italiani, fotografo, montatore, musicista",
                "immagine": "Se il link è da Wikipedia (wikipedia.org) NON mettere l'immagine nell'infobox",
                "film_italiano": "Se il film è italiano, il titolo è già in italiano - NON aggiungere titolo originale",
                "cast_integrato": "Per film italiani, il cast si integra nel testo principale, NON in una sezione separata",
                "categorie_film": "Aggiungere categorie: [[Categoria:Film italiani del YYYY]], [[Categoria:Film drammatici italiani]], [[Categoria:Film diretti da [regista]]]"
            },
            "bio_nazionalita": {
                "regola": "{{Bio}} ha un elenco predefinito di nazionalità - usare solo quelle riconosciute",
                "esempio": "britannico-nigeriano non funziona - usare solo 'britannico' o proporre aggiunta",
                "nota": "Per persone con doppia nazionalità, usare quella principale o una sola"
            },
            "bio_attivita": {
                "regola": "{{Bio}} ha un elenco predefinito di attività - usare solo quelle riconosciute",
                "esempio": "artista visivo non funziona - usare 'regista' oppure 'sceneggiatore'",
                "nota": "Non aggiungere attività non standard; scegliere dalla lista ufficiale"
            },
            "bio_guida_completa": {
                "parametri_obbligatori": "Attività, Nazionalità",
                "parametri_semplici": "Nome, Cognome, Sesso (M/F), LuogoNascita (solo città, no wikilink), GiornoMeseNascita (es: '13 settembre'), AnnoNascita (solo anno), LuogoMorte, GiornoMeseMorte, AnnoMorte, Epoca (2000, 1900, etc), PostNazionalità (senza punto finale)",
                "parametri_avanzati": "LuogoNascitaLink (se diverso da LuogoNascita), LuogoMorteLink (se diverso da LuogoMorte), Attività2, Attività3 (max 3 attività), NazionalitàNaturalizzato, Cittadinanza, Immagine, Didascalia, Didascalia2",
                "categorie_automatiche": "Il template {{Bio}} genera AUTOMATICAMENTE le categorie - NON aggiungere manualmente",
                "attivita_nazionalita": "Devono essere dall'elenco riconosciuto - usare minuscolo e concordanza di genere (es: 'regista' per uomo, 'regista' femminile se donna)",
                "luogo_nascita": "Solo il nome della città senza wikilink (es: 'Roma' non '[[Roma]]')",
                "giorni_mesi": "Formato: '13 settembre' (senza wikilink, il template lo aggiunge automaticamente)",
                "anni": "Solo l'anno (es: '1982' non '[[1982]]')",
                "post_nazionalita": "Precisazioni dopo nazionalità - NO punto finale, NO spazio iniziale - il template aggiunge automaticamente",
                "wikilink": "NON usare wikilink nei parametri principali del template"
            }
        }

    def fetch_wikipedia_page(self, page_title: str, lang: str = "en") -> str:
        """Fetches wiki markup from Wikipedia"""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "revisions",
            "rvprop": "content",
            "format": "json"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            pages = data.get("query", {}).get("pages", {})

            for page_id, page_data in pages.items():
                if "missing" in page_data:
                    return ""
                revisions = page_data.get("revisions", [])
                if revisions:
                    return revisions[0]["*"]
            return ""
        except Exception as e:
            print(f"Errore nel fetching: {e}")
            return ""

    def extract_infobox(self, wiki_markup: str) -> Tuple[str, int, int]:
        """Estrae l'infobox dal markup wiki"""
        pattern = r"(\{\{[Ii]nfobox[^}]*\}\})"
        match = re.search(pattern, wiki_markup, re.DOTALL)
        if match:
            return match.group(1), match.start(), match.end()
        return "", -1, -1

    def convert_infobox_to_bio(self, infobox_en: str) -> str:
        """Converte {{Infobox person}} inglese in {{Bio}} italiano"""

        # Mapping campi da Infobox person a Bio
        field_mapping = {
            r"\|\s*name\s*=": "|Nome = ",
            r"\|\s*image\s*=": "|Immagine = ",
            r"\|\s*caption\s*=": "|Didascalia = ",
            r"\|\s*birth_date\s*=": "|GiornoMeseNascita = ",
            r"\|\s*birth_place\s*=": "|LuogoNascita = ",
            r"\|\s*nationality\s*=": "|Nazionalità = ",
            r"\|\s*occupation\s*=": "|Attività = ",
        }

        bio = infobox_en.replace("{{Infobox person", "{{Bio")
        bio = bio.replace("{{infobox person", "{{Bio")

        for en_field, it_field in field_mapping.items():
            bio = re.sub(en_field, it_field, bio, flags=re.IGNORECASE)

        # Rimuovi parametri non validi per Bio
        invalid_params = [
            r"\|\s*birth_name\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*death_date\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*death_place\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*education\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*years_active\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*known_for\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*notable_works\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*spouse\s*=.*?(?=\n\||\n\}\})",
            r"\|\s*website\s*=.*?(?=\n\||\n\}\})",
        ]

        for param in invalid_params:
            bio = re.sub(param, "", bio, flags=re.IGNORECASE | re.DOTALL)

        # Rimuovi LuogoNascitaLink se uguale a LuogoNascita
        bio = self._remove_duplicate_luogo_nascita_link(bio)

        return bio

    def _remove_duplicate_luogo_nascita_link(self, bio: str) -> str:
        """Rimuove LuogoNascitaLink se duplicato con LuogoNascita"""
        luogo_match = re.search(r"\|LuogoNascita\s*=\s*([^\n|]+)", bio)
        link_match = re.search(r"\|LuogoNascitaLink\s*=\s*([^\n|]+)", bio)

        if luogo_match and link_match:
            luogo_value = luogo_match.group(1).strip()
            link_value = link_match.group(1).strip()

            if luogo_value == link_value:
                bio = re.sub(r"\|LuogoNascitaLink\s*=\s*[^\n|]+\n?", "", bio)

        return bio

    def extract_opening_text(self, wiki_markup: str) -> str:
        """Estrae il testo descrittivo iniziale (incipit)"""
        # Trova il primo paragrafo dopo l'infobox/template Bio
        # Esclude link wiki e formattazione
        pattern = r"\}\}\s*\n\n(.*?)(?:\n==|\Z)"
        match = re.search(pattern, wiki_markup, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Rimuovi '''''' e altri caratteri di formattazione
            text = re.sub(r"'''(.*?)'''", r"\1", text)
            # Rimuovi riferimenti <ref>
            text = re.sub(r"<ref>.*?</ref>", "", text, flags=re.DOTALL)
            return text.strip()
        return ""

    def add_post_nazionalita(self, bio: str, description: str) -> str:
        """Aggiunge il testo descrittivo al campo PostNazionalità"""
        # Cerca la riga Nazionalità e aggiunge PostNazionalità dopo
        insert_pattern = r"(\|Nazionalità\s*=\s*[^\n]+\n)"
        replacement = r"\1|PostNazionalità = " + description + "\n"
        return re.sub(insert_pattern, replacement, bio)

    def convert_cite_web_to_italian(self, wiki_markup: str) -> str:
        """Converte {{cite web}} inglese a {{Cita web}} italiano"""
        # Mapping parametri da inglese a italiano
        cite_mapping = {
            r"\{\{cite web": "{{Cita web",
            r"\|title=": "|titolo=",
            r"\|website=": "|sito=",
            r"\|access-date=": "|accesso=",
            r"\|date=": "|data=",
            r"\|first=": "|autore=",  # Semplificato
            r"\|last=": "|autore=",   # Semplificato
            r"\|author=": "|autore=",
            r"\|publisher=": "|editore=",
            r"\|language=": "|lingua=",
            r"\|url=": "|url=",
        }

        result = wiki_markup
        for en_param, it_param in cite_mapping.items():
            result = re.sub(en_param, it_param, result, flags=re.IGNORECASE)

        return result

    def fix_university_names(self, wiki_markup: str) -> str:
        """Corregge nomi di università - deve avere 'di' prima della città"""
        # Mapping università comuni
        university_mapping = {
            r"\[\[Università Stanford\]\]": "[[Università di Stanford]]",
            r"\[\[Stanford University\]\]": "[[Università di Stanford]]",
            r"\[\[Università York\]\]": "[[Università di York]]",
            r"\[\[Università Harvard\]\]": "[[Università di Harvard]]",
            r"\[\[Università MIT\]\]": "[[Università del Massachusetts - Massachusetts Institute of Technology]]",
        }

        result = wiki_markup
        for en_name, it_name in university_mapping.items():
            result = re.sub(en_name, it_name, result, flags=re.IGNORECASE)

        return result

    def fix_wikilinks(self, wiki_markup: str) -> str:
        """Corregge wikilink inglesi con i corrispettivi italiani"""
        # Mapping di wikilink da inglese a italiano
        # Includere solo link che differiscono significativamente
        wikilink_mapping = {
            r"\[\[BAFTA Award for Outstanding Debut by a British Writer, Director or Producer\|":
                "[[BAFTA al miglior esordio britannico da regista, sceneggiatore o produttore|",
            r"\[\[British Independent Film Award for Best Director\|":
                "[[British Independent Film Award per il miglior regista|",
            r"\[\[Gotham Independent Film Award for Breakthrough Director\|":
                "[[Gotham Independent Film Award per il regista emergente|",
        }

        result = wiki_markup
        for en_link, it_link in wikilink_mapping.items():
            result = re.sub(en_link, it_link, result, flags=re.IGNORECASE)

        return result

    def translate_with_claude(self, text: str, context: str = "") -> str:
        """Usa Claude per tradurre testo da inglese a italiano"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Traduci questo testo da Wikipedia dall'inglese all'italiano, mantenendo la formattazione wiki (wikilink, grassetto, corsivo):

{text}

{f'Contesto: {context}' if context else ''}

Rispondi SOLO con il testo tradotto, senza spiegazioni."""
                    }
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Errore Claude traduzione: {e}")
            return text

    def extract_bio_info_with_claude(self, opening_text: str, page_title: str) -> Dict:
        """Usa Claude per estrarre info per template Bio"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Dalla descrizione di "{page_title}", estrai in JSON:
- nazionalita (es: "statunitense")
- attivita (es: "regista", "produttore", "attore")
- anno_nascita (numero, es: 1962)
- post_nazionalita (descrizione breve della persona in italiano)

Testo:
{opening_text}

Rispondi SOLO con JSON valido."""
                    }
                ]
            )
            try:
                return json.loads(message.content[0].text)
            except:
                return {}
        except Exception as e:
            print(f"Errore Claude Bio extraction: {e}")
            return {}

    def verify_wikilinks_with_claude(self, text: str) -> str:
        """Usa Claude per verificare e correggere wikilink al formato italiano"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Verifica i wikilink in questo testo wiki. Per ogni link:
- Se è un nome di attore/regista con "(actor)" o "(director)", rimuovi
- Se è un premio/festival, usa il nome italiano corretto
- Se è un'università, assicurati sia nel formato "Università di [città]"

Testo:
{text}

Rispondi SOLO con il testo corretto."""
                    }
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Errore Claude wikilink: {e}")
            return text

    def suggest_categories_with_claude(self, page_title: str, occupation: str, nationality: str) -> List[str]:
        """Usa Claude per suggerire categorie italiane"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Per una persona italiana Wikipedia con:
- Nome: {page_title}
- Nazionalità: {nationality}
- Attività: {occupation}

Suggerisci 3-4 categorie italiane appropriate (formato: [[Categoria:...]]).
Rispondi SOLO con le categorie, una per riga."""
                    }
                ]
            )
            cats = message.content[0].text.strip().split('\n')
            return [c.strip() for c in cats if c.strip()]
        except Exception as e:
            print(f"Errore Claude categories: {e}")
            return []

    def translate_page(self, page_title: str, use_claude: bool = True) -> str:
        """Traduce una pagina Wikipedia dall'inglese all'italiano"""
        # Fetch pagina inglese
        wiki_markup = self.fetch_wikipedia_page(page_title, lang="en")
        if not wiki_markup:
            return f"Errore: pagina '{page_title}' non trovata"

        print(f"✓ Pagina caricata ({len(wiki_markup)} caratteri)")

        # Estrai testo di apertura per Claude
        opening_text = self.extract_opening_text(wiki_markup)

        # Estrai infobox
        infobox, start, end = self.extract_infobox(wiki_markup)

        if infobox:
            # Converti infobox a Bio italiano
            bio_italiano = self.convert_infobox_to_bio(infobox)

            # Sostituisci infobox originale con Bio
            wiki_markup = wiki_markup[:start] + bio_italiano + wiki_markup[end:]
            print("✓ Template Bio convertito")

        # Applica conversioni globali
        wiki_markup = self.convert_cite_web_to_italian(wiki_markup)
        wiki_markup = self.fix_university_names(wiki_markup)
        wiki_markup = self.fix_wikilinks(wiki_markup)
        print("✓ Conversioni automatiche applicate (cite web, università, wikilink)")

        # Sostituisci {{Reflist}} con <references/>
        wiki_markup = re.sub(r"\{\{[Rr]eflist\}\}", "<references/>", wiki_markup)

        # Rimuovi DEFAULTSORT (generato automaticamente da Bio)
        wiki_markup = re.sub(r"\{\{DEFAULTSORT:[^}]+\}\}\n?", "", wiki_markup, flags=re.IGNORECASE)

        # Usa Claude per miglioramenti
        if use_claude and opening_text:
            print("\n🤖 Claude elabora informazioni...")

            # Estrai info Bio
            bio_info = self.extract_bio_info_with_claude(opening_text, page_title)
            if bio_info:
                print(f"  ✓ Info Bio estratte: {bio_info}")

            # Traduci testo di apertura (solo prima parte per demo)
            first_paragraph = opening_text.split('\n\n')[0] if '\n\n' in opening_text else opening_text
            if len(first_paragraph) < 500:  # Solo se ragionevole
                translated = self.translate_with_claude(first_paragraph)
                if translated and translated != first_paragraph:
                    wiki_markup = wiki_markup.replace(first_paragraph, translated)
                    print(f"  ✓ Paragrafo tradotto")

        return wiki_markup

    def print_rules(self):
        """Stampa le regole applicate"""
        print("\n=== REGOLE APPLICATE ===")
        for rule, details in self.rules.items():
            print(f"\n{rule}:")
            for key, value in details.items():
                print(f"  - {key}: {value}")

# Uso
if __name__ == "__main__":
    import sys

    translator = WikipediaTranslator()

    if len(sys.argv) > 1:
        page_title = " ".join(sys.argv[1:])
        print(f"Traduzione di: {page_title}\n")
        result = translator.translate_page(page_title)
        print(result)
    else:
        translator.print_rules()
        print("\n=== UTILIZZO ===")
        print("python wikipedia_translator.py 'Titolo Pagina'")
