import csv
import html
import os

from google.cloud import translate_v3
from openai import OpenAI

google_project_id = os.environ.get("GOOGLE_PROJECT_ID", "euclid-449115")
google_credentials_set = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
google_client = translate_v3.TranslationServiceClient() if google_credentials_set else None

openai_api_key = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(
    api_key=openai_api_key
) if openai_api_key else None


def google_translate(texts):
    if not google_client:
        return [""] * len(texts), ""
    try:
        parent = f"projects/{google_project_id}/locations/global"
        request = {
            "parent": parent,
            "contents": [t for t in texts if t != ""],
            "target_language_code": "en",
        }
        response = google_client.translate_text(request=request)
        translations = response.translations
        result = []
        j = 0
        for t in texts:
            if t == "":
                result.append("")
            else:
                result.append(html.unescape(translations[j].translated_text))
                j += 1
        languages = {t.detected_language_code for t in response.translations}
        return result, languages
    except Exception as e:
        print("!!! Error translating text", e)


def openai_query(question, text, instructions, max_tokens=50, creativity=0):
    if not openai_client:
        return ""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": question},
                {"role": "user", "content": text},
                {"role": "system", "content": instructions},
            ],
            max_tokens=max_tokens,
            temperature=creativity
        )
        if len(response.choices) != 1:
            print("!!! Unexpected response from OpenAI", response)
        if response.choices[0].finish_reason != 'stop':
            print("!!! OpenAI did not finish processing the request", response)
        return response.choices[0].message.content
    except Exception as e:
        print("!!! Error querying OpenAI", e)

def write_csv(entries, fpath):
    with open(fpath, mode="w", newline="", encoding="utf-8") as f:
        all_fields = {k for r in entries for k in r.keys()}
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
        writer.writeheader()
        for row in entries:
            writer.writerow(row)

def read_csv(fpath):
    with open(fpath, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]
