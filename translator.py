import json


class Translator:
    def __init__(self, language='en', language_file='language.json'):
        self.translations = {}
        self.language = language
        self.load_language_file(language_file)

    def load_language_file(self, language_file):
        with open(language_file, 'r') as file:
            self.translations = json.load(file)

    def set_language(self, language):
        self.language = language

    def translate(self, key, language=None):
        if language is None:
            language = self.language
        return self.translations.get(language, {}).get(key, key)
