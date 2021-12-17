import argparse
import logging
import re
from typing import Optional

import orjson
import tqdm
from russian_g2p.Grapheme2Phoneme import Grapheme2Phoneme

_logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

_STRESS_CODE = 769
_PLUS_CODE = 43
_JO_CODE = 1105
_VOWELS = 'уеёыаоэяию'
_VOWEL_CODES = {ord(c) for c in _VOWELS}
_STRESS_PHONEMES = {'U0', 'O0', 'A0', 'E0', 'Y0', 'I0', 'U0l', 'O0l', 'A0l', 'E0l', 'Y0l', 'I0l'}


def _parse_args():
    parser = argparse.ArgumentParser(description='Adds phonemes and stress position information to '
                                     'the word stresses file, obtained via '
                                     'scripts/crawl_word_stresses.py script.')
    parser.add_argument('--word-stresses-file-path', '-s', type=str, required=True)
    parser.add_argument('--out-file-path', '-o', type=str, required=True)
    return parser.parse_args()


def main(word_stresses_file_path, out_file_path):
    g2p = Grapheme2Phoneme()
    with open(word_stresses_file_path) as inp_file, open(out_file_path, 'wb') as out_file:
        for line in tqdm.tqdm(inp_file, desc='Words'):
            data = orjson.loads(line)
            word = _prepare_word_for_phonemization(data['word'])
            if not word:
                continue

            try:
                phonemes = g2p.word_to_phonemes(word)
            except AssertionError:
                continue

            stress_idx = _get_stress_idx(phonemes)
            if stress_idx is None:
                continue

            data.update({'word': word, 'phonemes': phonemes, 'stress_idx': stress_idx})
            payload = orjson.dumps(data)
            out_file.write(payload)
            out_file.write(b'\n')


def _prepare_word_for_phonemization(word) -> Optional[str]:
    if '-' in word:
        return None

    word = word.strip()
    single_vowel = True if len(re.findall(f'[{_VOWELS}]', word)) == 1 else False
    codes = [ord(char) for char in word]
    n_stress_codes = sum(code == _STRESS_CODE for code in codes)
    n_jos_codes = sum(code == _JO_CODE for code in codes)
    if n_stress_codes > 1 or (n_stress_codes == 0 and n_jos_codes > 1):
        return None

    new_codes = []
    for code in codes:
        if code in _VOWEL_CODES and single_vowel:
            new_codes.append(code)
            new_codes.append(_PLUS_CODE)
        elif code == _STRESS_CODE:
            new_codes.append(_PLUS_CODE)
        elif code == _JO_CODE and n_stress_codes == 0:
            new_codes.append(_JO_CODE)
            new_codes.append(_PLUS_CODE)
        else:
            new_codes.append(code)

    word = ''.join(chr(c) for c in new_codes)
    word = re.sub(r'\++', '+', word)
    return word


def _get_stress_idx(phonemes) -> Optional[int]:
    stress_idx = None
    for i_phoneme, phoneme in enumerate(phonemes):
        if phoneme in _STRESS_PHONEMES:
            if stress_idx is not None:
                _logger.warning(f'There are several stress phonemes: {phonemes}...')
                return None
            stress_idx = i_phoneme

    if stress_idx is None:
        _logger.warning(f'There are no stress phonemes: {phonemes}...')
        return None

    return stress_idx


if __name__ == '__main__':
    args = _parse_args()
    main(
        word_stresses_file_path=args.word_stresses_file_path,
        out_file_path=args.out_file_path,
    )
