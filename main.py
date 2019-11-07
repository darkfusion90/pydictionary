import os
import time
import textwrap
from random import randint
import re
import requests
import bs4
from bs4 import BeautifulSoup
import wiktionaryparser
import json

SCRIPT_DIR = os.path.dirname(os.path.realpath('__file__'))
OFFLINE_DICT_FILE = os.path.join(SCRIPT_DIR, 'dictionary.json')

PARTS_OF_SPEECH = ['noun', 'pronoun', 'adjective', 'determiner',
                   'verb', 'adverb', 'preposition', 'conjunction', 'interjection']


class PyDictionary:
    def __init__(self):
        self.parsed_output = str('')

    def define_word(self, word):
        word = word.lower()
        print('Looking up definition offline...')
        time.sleep(2)

        word_data, word_found = self.fetch_word_data_offline(word)

        if not word_found:
            print("Couldn't find definition offline...")
            time.sleep(1)
            print('Looking up online...')
            word_data, word_found = self.fetch_word_data_online(word)

            if word_found:
                self.add_word_to_offline_dict(word, word_data)
            else:
                print(
                    "Definition of {} not found. Please check the spelling and/or the language.".format(word))
                return

        self.parsed_output += self.bold_word(word)
        self.parse_pronunciations(word_data)
        self.parse_etymology(word_data)
        self.parse_definitions(word_data)
        self.display_parsed_output()

    def bold_word(self, word):
        return '\n\033[1m' + word + '\033[0m';

    def fetch_word_data_offline(self, word):
        dictionary = json.load(
            fp=open(OFFLINE_DICT_FILE, mode='r', encoding='utf-8'))

        for current_word_dict in dictionary:
            if word in list(current_word_dict.keys()):
                return (current_word_dict[word], True)

        return (dict(''), False)

    def fetch_word_data_online(self, word):
        parser = wiktionaryparser.WiktionaryParser()
        word_data = parser.fetch(word)

        if (len(word_data) == 0) or not (self.word_exists(word_data[0])):
            return (dict(''), False)

        return (word_data[0], True)

    def parse_etymology(self, word_data):
        etymology = word_data['etymology']
        if len(etymology) == 0:
            return

        enable_color_code = '\033[1;33;40m'
        disable_color_code = '\033[0;0m'
        prefix = 'Etymology:'
        init_indent = enable_color_code + prefix + disable_color_code + '\n\t'

        wrapper = textwrap.TextWrapper(
            initial_indent=init_indent, subsequent_indent='\t', width=100)
        output = wrapper.fill(etymology)
        self.parsed_output += output + '\n\n'

    def parse_definitions(self, word_data):
        definitions = word_data['definitions']
        for definition in definitions:
            self.parse_part_of_speech(definition)
            self.parse_texts(definition)
            self.parse_related_words(definition)
            self.parse_examples(definition)

    def parse_pronunciations(self, word_data):
        text_pronunciations = word_data['pronunciations']['text']
        for text_pronun in text_pronunciations:
            re_match = re.search(r'IPA: .+', text_pronun)
            if re_match == None:
                continue
            else:
                self.parsed_output += '  ' + re_match.group().replace('IPA: ', '') + '\n'
                return
        self.parsed_output += '\n'

    def parse_part_of_speech(self, definition):
        color_enable = '\033[0;92;4m'
        color_disable = '\033[0;0m'

        self.parsed_output += color_enable
        self.parsed_output += definition['partOfSpeech'].title() + ':'
        self.parsed_output += color_disable + '\n'

    def parse_texts(self, definition):
        output = ''
        text_count = 1
        for text in definition['text']:
            prefix = str(text_count) + ". "
            wrapper = textwrap.TextWrapper(
                initial_indent="\t" + prefix, subsequent_indent='\t' + (' ' * len(prefix)), width=100)

            output += wrapper.fill(text) + "\n"
            text_count += 1

        self.parsed_output += output

    def parse_related_words(self, definition):
        related_words = definition['relatedWords']
        if len(related_words) == 0:
            return

        output = '\n'
        for related_word in related_words:
            rel_type = related_word['relationshipType']
            prefix = '\t' + rel_type + ': '
            italicized_prefix = '\033[3m' + prefix + '\033[0m'

            wrapper = textwrap.TextWrapper(
                initial_indent=italicized_prefix, subsequent_indent='\t' + ' ' * len(prefix), width=100)
            string = ''
            for word in related_word['words']:
                if 'See also Thesaurus' in word:
                    continue
                string += word + ' '

            output += wrapper.fill(string) + '\n\n'

        self.parsed_output += output.strip() + '\n'

    def parse_examples(self, definition):

        examples = definition['examples']
        if len(examples) == 0:
            return

        selected_example = examples[0]
        for example in examples:
            if 10 < len(example) < len(selected_example):
                selected_example = example

        wrapper = textwrap.TextWrapper(
            initial_indent='\t', subsequent_indent='\t', width=100)
        self.parsed_output += '\n\033[3m'
        self.parsed_output += wrapper.fill(selected_example) + '\033[0m\n'

    def display_parsed_output(self):
        print(self.parsed_output, end="")

    def word_exists(self, word_data):
        if (len(list(word_data.keys())) == 0):
            return False

        audio_pronunciation = word_data['pronunciations']['audio']
        text_pronunciation = word_data['pronunciations']['text']
        has_pronunciation = len(audio_pronunciation) != 0 or len(
            text_pronunciation) != 0

        has_etymology = len(word_data['etymology']) != 0
        has_definitions = len(word_data['definitions']) != 0
        return (has_pronunciation or has_etymology or has_definitions)

    def add_word_to_offline_dict(self, word, word_data):
        file_data = list('')
        with open(OFFLINE_DICT_FILE, mode='r', encoding='utf-8') as file:
            file_data = json.load(file)

        if self.word_exists_in_offline_dict(word, file_data):
            return

        file_data.append(dict({word: word_data}))
        with open(OFFLINE_DICT_FILE, mode='w', encoding='utf-8') as file:
            json.dump(file_data, file)

    def word_exists_in_offline_dict(self, word, offline_dict_file_data):
        for word_data in offline_dict_file_data:
            if (list(word_data.keys()).count(word) == 1):
                return True
        return False


'''with open('words_alpha.txt') as file:
    for line in file:
        line = line.strip()
        pd = PyDictionary()
        pd.define_word(line)'''

if __name__ == '__main__':
    pd = PyDictionary()
    pd.define_word(input())
