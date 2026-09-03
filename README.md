# Wikipedia Translator: English to Italian

Script Python per tradurre automaticamente voci Wikipedia dall'inglese all'italiano, mantenendo tutte le convenzioni e i template di Wikipedia italiana.

## Caratteristiche

Lo script applica automaticamente le seguenti regole:

### Template
- ✅ **{{Bio}}** per le persone (non {{Infobox persona}})
- ✅ **{{Film}}** per i film (non {{Infobox film}})
- ✅ **{{Cita web}}** e **{{Cita news}}** italiani (non {{cite web}})
- ✅ **<references/>** al posto di {{Reflist}}
- ✅ NO {{DEFAULTSORT:...}} (generato automaticamente da {{Bio}})

### Parametri {{Bio}}
- ✅ LuogoNascitaLink solo se diverso da LuogoNascita
- ✅ PostNazionalità SENZA punto finale (il template lo aggiunge)
- ✅ NO wikilink nei parametri principali
- ✅ Categorie generate automaticamente - NON aggiungere manualmente
- ✅ Attività e Nazionalità da lista predefinita riconosciuta
- ✅ Minuscolo e concordanza di genere per attività/nazionalità

### Convenzioni italiane
- ✅ **Università di [città]** non Università [città]
- ✅ **== Biografia ==** come prima sezione (non == Primi anni ==)
- ✅ **== Carriera ==** come sezione delle opere
- ✅ Wikilink verificati in italiano (rimosso "(actor)" da attori, etc)
- ✅ Link a premi/festival tradotti al corrispettivo italiano

### Citazioni
- ✅ Parametri italiani: titolo, sito, data, autore, accesso, lingua
- ✅ NO punto alla fine di PostNazionalità
- ✅ Formato date italiane: "13 settembre" (no wikilink, il template lo aggiunge)
- ✅ Anni senza wikilink: "1982"

### Template Film
- ✅ NO immagine nell'infobox se il link è da Wikipedia (wikipedia.org)
- ✅ Parametri: titolo, titolo originale, paese, anno uscita, durata, genere, regista

## Utilizzo

```python
from wikipedia_translator import WikipediaTranslator

translator = WikipediaTranslator()

# Fetching pagina Wikipedia inglese
wiki_markup = translator.fetch_wikipedia_page("Elizabeth Lo")

# Convertire {{Infobox person}} → {{Bio}}
infobox, start, end = translator.extract_infobox(wiki_markup)
bio_italiano = translator.convert_infobox_to_bio(infobox)

# Convertire {{cite web}} → {{Cita web}}
wiki_markup_tradotto = translator.convert_cite_web_to_italian(wiki_markup)

# Fissare nomi università
wiki_markup_tradotto = translator.fix_university_names(wiki_markup_tradotto)

# Fissare wikilink
wiki_markup_tradotto = translator.fix_wikilinks(wiki_markup_tradotto)
```

## Regole memorizzate

Tutte le regole sono documentate nel dizionario `self.rules` della classe `WikipediaTranslator`.

## Versione

v1.0.0 - Regole complete per traduzione Wikipedia en → it

## Autore

Claude Code - Wikipedia Translator
