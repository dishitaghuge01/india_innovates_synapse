import spacy
import json
import os

INPUT_PATH = "data/processed/clean_articles.json"
OUTPUT_PATH = "data/processed/extracted_entities.json"

nlp = spacy.load("en_core_web_sm")


def load_articles():

    if not os.path.exists(INPUT_PATH):
        print("Clean articles not found")
        return []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_entities_from_text(text):

    doc = nlp(text)

    entities = []

    for ent in doc.ents:

        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    return entities


def extract_entities(articles):

    results = []

    for article in articles:

        text_content = article.get("content", "")
        text_title = article.get("title", "")

        # Extract from content
        entities = extract_entities_from_text(text_content)
        # Extract from title
        entities += extract_entities_from_text(text_title)

        # Optional: deduplicate
        seen = set()
        deduped_entities = []
        for ent in entities:
            key = (ent['text'], ent['label'])
            if key not in seen:
                deduped_entities.append(ent)
                seen.add(key)

        results.append({
            "title": article.get("title"),
            "url": article.get("url"),
            "content": text_content,
            "entities": deduped_entities
        })

    return results



def save_entities(results):

    os.makedirs("data/processed", exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def run_entity_extraction():

    print("Loading clean articles...")

    articles = load_articles()

    print(f"Loaded {len(articles)} articles")

    print("Extracting entities...")

    results = extract_entities(articles)

    print("Saving extracted entities...")

    save_entities(results)

    print("Entity extraction completed")


if __name__ == "__main__":

    run_entity_extraction()
