"""Data loader of M-AILABS dataset, with only Jane Eyre"""
import os
import re
import codecs
import unicodedata
import numpy as np

from torch.utils.data import Dataset

vocab = "PE abcdefghijklmnopqrstuvwxyz0123456789!',-.:;?"  # P: Padding, E: EOS.
char2idx = {char: idx for idx, char in enumerate(vocab)}
idx2char = {idx: char for idx, char in enumerate(vocab)}

lang = 'en_UK'
speaker = 'female/elizabeth_klett'
books = [
    'jane_eyre'
]

def text_normalize(text):
    text = ''.join(char for char in unicodedata.normalize('NFD', text)
                   if unicodedata.category(char) != 'Mn')  # Strip accents

    text = text.lower()
    text = re.sub("[^{}]".format(vocab), " ", text)
    text = re.sub("[ ]+", " ", text)
    return text


def read_metadata(base_path):
    fnames, text_lengths, texts, i = [], [], [], 0
    for book in books:
        transcript = os.path.join(base_path, book, 'metadata.csv')
        lines = codecs.open(transcript, 'r', 'utf-8').readlines()
        for line in lines:
            if i <= 3000:
                fname, _, text = line.strip().split("|")

                if os.path.isfile(os.path.join(base_path, book, fname)):
                    fnames.append(fname)

                    text = text_normalize(text) + "E"  # E: EOS
                    text = [char2idx[char] for char in text]
                    text_lengths.append(len(text))
                    texts.append(np.array(text, np.long))

                    i += 1

    return fnames, text_lengths, texts


def get_test_data(sentences, max_n):
    normalized_sentences = [text_normalize(line).strip() + "E" for line in sentences]  # text normalization, E: EOS
    texts = np.zeros((len(normalized_sentences), max_n + 1), np.long)
    for i, sent in enumerate(normalized_sentences):
        texts[i, :len(sent)] = [char2idx[char] for char in sent]
    return texts


class EnUK(Dataset):
    def __init__(self, keys):
        dir_name = os.path.join(lang, 'by_book', speaker)

        self.keys = keys
        self.path = os.path.join(dir_name)
        self.fnames, self.text_lengths, self.texts = read_metadata(os.path.join(self.path))

    def slice(self, start, end):
        self.fnames = self.fnames[start:end]
        self.text_lengths = self.text_lengths[start:end]
        self.texts = self.texts[start:end]

    def __len__(self):
        return len(self.fnames)

    def __getitem__(self, index):
        data = {}
        if 'texts' in self.keys:
            data['texts'] = self.texts[index]
        if 'mels' in self.keys:
            # (39, 80)
            data['mels'] = np.load(os.path.join(self.path, 'mels', "%s.npy" % self.fnames[index]))
        if 'mags' in self.keys:
            # (39, 80)
            data['mags'] = np.load(os.path.join(self.path, 'mags', "%s.npy" % self.fnames[index]))
        if 'mel_gates' in self.keys:
            data['mel_gates'] = np.ones(data['mels'].shape[0], dtype=np.int)  # TODO: because pre processing!
        if 'mag_gates' in self.keys:
            data['mag_gates'] = np.ones(data['mags'].shape[0], dtype=np.int)  # TODO: because pre processing!
        return data

