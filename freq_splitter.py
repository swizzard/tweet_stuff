import json
with open("word_freqs.json") as f:
    word_freqs = json.load(f.read())

def split_text(text, word_frequencies, cache):
    """
    Adapted from http://stackoverflow.com/questions/2174093/python-word-splitting
    :param text: the string to split
    :type text: string
    :param word_frequencies: dictionary of words and their frequencies
    :type word_frequencies: dict
    :param cache: cache of splits and their confidences
    :type cache: dict (should be empty for original call)
    :return: tuple:
        freq (int)
        split string (list)
    """
    if text in cache:
        return cache[text]
    if not text:
        return 1, []
    best_freq, best_split = 0, []
    for i in xrange(1, len(text) + 1):
        word, remainder = text[:i], text[i:]
        freq = word_frequencies.get(word, None)
        if freq:
            remainder_freq, remainder = split_text(
                    remainder, word_frequencies, cache)
            freq *= remainder_freq
            if freq > best_freq:
                best_freq = freq
                best_split = [word] + remainder
    cache[text] = (best_freq, best_split)
    return cache[text]
