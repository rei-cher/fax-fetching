import spacy

def extract_names(text: str):
    nlp = spacy.load('en_core_web_sm')

    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    return names