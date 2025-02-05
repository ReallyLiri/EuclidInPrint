from lingua import Language

from tools import read_csv, google_translate, write_csv, openai_query

file_path = "docs/EiP.csv"

entries = read_csv(file_path)

_TRANSLATE = False
_EXTRACT_TITLE_VERBS = True
_EXTRACT_PUBLISHER = False
_EXTRACT_TITLE_FEATURES = False

for entry in entries:
    print(entry["key"])

    if _TRANSLATE and entries["language"] != Language.ENGLISH.name:
        translations, languages = (
            google_translate([entry["title"], entry["colophon"], entry["imprint"]])
        )
        entry["title_EN"], entry["colophon_EN"], entry["imprint_EN"] = translations
        entry["language_v2"] = " and ".join(languages)

    if _EXTRACT_TITLE_VERBS and Language.FRENCH.name in entry["language"] or Language.FRENCH.name in entry["language 2"]:
        verbs = openai_query(
            "Please extract all verbs in this text",
            entry["title"],
            "Plot only the verbs, as a simple list separated by comma",
            None,
        )
        entry["title_verbs"] = verbs

    if _EXTRACT_PUBLISHER:
        joined_body = "\n".join([entry["title"], entry["colophon"], entry["imprint"]]).strip()
        publisher = openai_query(
            "Who is the publisher mentioned in this title page?",
            joined_body,
            "Answer only with a de-latinized name or UNKNOWN if publisher is not mentioned."
        )
        if publisher != "UNKNOWN":
            entry["publisher"] = publisher

    if _EXTRACT_TITLE_FEATURES:
        features = openai_query(
            "Please extract following properties, if available, from this 16-17th century title page: basic introduction, content description (separate to multiple description sections if necessary), process in which the book was established, author name, author description, publisher name, publisher description, mentions of Euclid, mentions of other names, privileges, dedications, mentions of translated-from, mentions of translated-to",
            entry["title"],
            "Use json format to output the entrys. Keys will be the extracted properties. In the json values, keep original text. No need to specify values if property is not found in the text. Plot each property in a separate section. If a property is not available, leave it empty. In case of a property that mentions a description, separate to multiple description sections if necessary using a json array.",
            None,
            0.3
        ).replace("```json", "").replace("```", "")
        entry["title_features"] = features

write_csv(entries, file_path)
