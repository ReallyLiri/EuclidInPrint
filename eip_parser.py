import re

from docx import Document
from lingua import LanguageDetectorBuilder, Language

from tools import write_csv

langs = [
    Language.LATIN, Language.FRENCH, Language.GERMAN, Language.GREEK, Language.ARABIC,
    Language.SPANISH, Language.ITALIAN, Language.ENGLISH, Language.DUTCH, Language.CHINESE
]
detector = LanguageDetectorBuilder.from_languages(*langs).build()

entry_start_pattern = r"^([A-Za-zÄÖÜäöüß/\s]+\s)+\d{4}([/\–]\d{2,4})?[a-z]?$"

input_file_path = "docs/EiP.docx"
output_file_path = "docs/EiP.csv"

print(f"Extracting text from the document: {input_file_path}")

doc = Document(input_file_path)
full_text = []

for i, para in enumerate(doc.paragraphs, 1):
    full_text.append(para.text)

print(f"Extracted {len(full_text)} paragraphs from the document")

FORMATS = ["folio", "octavo", "quarto", "?quarto", "16mo", "duodecimo", "sexto", "octodecimo"]
POST_TITLE_PREFIXES = ["Colophon:", "Imprint:", "Elements 1–6"]


def _has_format(text):
    return any(fmt for fmt in FORMATS if text.lower().startswith(fmt) or f" {fmt}" in text.lower()) and not "nunc quarto editi" in text


def _has_post_title_prefix(text):
    return any(prefix for prefix in POST_TITLE_PREFIXES if text.startswith(prefix))


def _extract_author(text):
    return text.replace(" ed", "") if text.endswith(" ed") else ""


def _dedup_languages(langs):
    if Language.ENGLISH.name in langs:
        return [Language.ENGLISH.name]
    if Language.SPANISH.name in langs and Language.LATIN.name in langs:
        langs.remove(Language.SPANISH.name)
    if Language.ENGLISH.name in langs and Language.LATIN.name in langs:
        langs.remove(Language.ENGLISH.name)
    if Language.ITALIAN.name in langs and Language.LATIN.name in langs:
        langs.remove(Language.ITALIAN.name)
    if Language.DUTCH.name in langs and Language.GERMAN.name in langs:
        langs.remove(Language.GERMAN.name)
    if Language.FRENCH.name in langs:
        for l in langs:
            if l != Language.FRENCH.name and l != Language.LATIN.name and l != Language.GREEK.name:
                langs.remove(l)
    return langs


results = []


def _parse_catalog_para(texts):
    try:
        result = {
            "title": "",
            "colophon": "",
            "imprint": "",
            "title_EN": "",
            "colophon_EN": "",
            "imprint_EN": "",
            "publisher": "",
            "format": "",
            "books": ""
        }

        key = texts[0]
        result["key"] = key
        year_index = key.index("1")

        result["city"] = key[:year_index].strip()
        result["year"] = re.sub(r'[a-z]+$', '', key[year_index:].strip())

        def _try_section(i, prefix, prop, early_break):
            if texts[i].startswith(prefix):
                result[prop] = texts[i].replace(prefix, "").strip()
                i += 1
            elif early_break:
                return i
            for text in texts[i:]:
                if _has_post_title_prefix(text) or _has_format(text):
                    break
                result[prop] = (result.get(prop, "") + "\n" + text).strip()
                i += 1
            return i

        i = 1
        for text in texts[1:]:
            if _has_post_title_prefix(text) or _has_format(text):
                break
            result["title"] = (result.get("title", "") + "\n" + text).strip()
            i += 1

        i = _try_section(i, "Imprint:", "imprint", True)
        i = _try_section(i, "Colophon:", "colophon", False)
        i = _try_section(i, "Imprint:", "imprint", False)

        joined_body = "\n".join([result["title"], result["colophon"], result["imprint"]])
        languages = detector.detect_multiple_languages_of(joined_body)
        result["language"] = " and ".join(_dedup_languages(sorted({
            l.language.name for l
            in languages
            if l.word_count > 5 or len(languages) == 1
        })))

        if any(fmt for fmt in FORMATS if fmt in texts[i].lower()):
            split = texts[i].split(".")
            result["format"] = split[0].strip()
            result["books"] = split[1].strip()
            result["par"] = _extract_author(split[2].strip())
        else:
            split = texts[i].split(".")
            result["books"] = split[0].strip()
            result["par"] = _extract_author(split[1].strip())

        results.append(result)

    except Exception as e:
        print("!!! Error parsing entry", e, texts)


in_catalog_range = False
current_entry = []

for i, para in enumerate(full_text, 1):
    if not in_catalog_range:
        if para == "Catalogue":
            print(f"Found 'Catalogue' at paragraph {i}")
            in_catalog_range = True
    else:
        if para == "Appendices":
            print(f"Found 'Appendices' at paragraph {i}")
            break
        if para == "":
            continue
        if re.fullmatch(entry_start_pattern, para):
            print(para)
            if len(current_entry) > 0:
                _parse_catalog_para(current_entry)
            current_entry = [para]
        else:
            current_entry.append(para)


write_csv(results, output_file_path)
