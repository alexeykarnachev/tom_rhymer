from tom_rhymer.rhymer import Rhymer
from argparse import ArgumentParser


def _parse_args():
    parser = ArgumentParser(description='Trains Rhymer from prepared phonemes file.')
    parser.add_argument(
        '--word-phonemes-file-path',
        '-p',
        type=str,
        required=True,
        help='Path to the words phonemes file, prepared by scripts/phonemize_words.py script.')
    parser.add_argument(
        '--allowed-words-file-path',
        '-a',
        type=str,
        required=True,
        help='Path to the white list of words to be used in rhymer (one line - one word).')
    parser.add_argument(
        '--rhymer-file-path', '-r', type=str, required=True, help='Output path to the pickled Rhymer object.')
    return parser.parse_args()


def main(word_phonemes_file_path, allowed_words_file_path, rhymer_file_path):
    allowed_words = []
    with open(allowed_words_file_path) as inp_file:
        for line in inp_file:
            word = line.strip()
            allowed_words.append(word)
    allowed_words = set(allowed_words)

    rhymer = Rhymer()
    rhymer.train(word_phonemes_file_path, allowed_words)
    rhymer.save(rhymer_file_path)


if __name__ == '__main__':
    args = _parse_args()
    main(
        word_phonemes_file_path=args.word_phonemes_file_path,
        allowed_words_file_path=args.allowed_words_file_path,
        rhymer_file_path=args.rhymer_file_path,
    )
