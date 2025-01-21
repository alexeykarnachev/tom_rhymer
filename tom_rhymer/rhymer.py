import pickle
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain, cycle
from typing import Dict, List, Optional, Sequence, Set, Tuple

import orjson
import pkg_resources
import tqdm
from pymorphy3 import MorphAnalyzer
from russian_g2p.Grapheme2Phoneme import Grapheme2Phoneme

from tom_rhymer.tree import Tree

_RHYMER_FILE_PATH: str = pkg_resources.resource_filename(
    "tom_rhymer", "data/rhymer.pkl"
)

_morph: MorphAnalyzer = MorphAnalyzer()
_g2p: Grapheme2Phoneme = Grapheme2Phoneme()
_STRESS_PHONEMES: Set[str] = {
    "U0",
    "O0",
    "A0",
    "E0",
    "Y0",
    "I0",
    "U0l",
    "O0l",
    "A0l",
    "E0l",
    "Y0l",
    "I0l",
}


@dataclass
class Word:
    word: str
    roots: Set[str]

    def __hash__(self) -> int:
        return id(self.word)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, Word):
            return NotImplemented
        return self.word == rhs.word

    def __post_init__(self) -> None:
        if "+" not in self.word:
            raise ValueError(
                f"Word {self.word} in not stressed. `+` sign must be present."
            )

    def __str__(self) -> str:
        return re.sub(r"\++", "", self.word)


class Rhymer:
    _DEFAULT_PARAMS: List[Tuple[Tuple[int, int], Tuple[int, int]]] = [
        ((4, 4), (1, 0)),
        ((4, 4), (0, 1)),
        ((4, 3), (1, 0)),
        ((4, 3), (0, 1)),
        ((3, 4), (1, 0)),
        ((3, 4), (0, 1)),
        ((3, 3), (0, 0)),
        ((2, 2), (0, 0)),
    ]

    def __init__(self) -> None:
        self._left_tree: Tree = Tree()
        self._right_tree: Tree = Tree()
        self._words: List[Word] = []

    @property
    def words(self) -> List[Word]:
        return self._words

    def train(
        self, word_phonemes_file_path: str, allowed_words: Optional[Set[str]]
    ) -> None:
        with open(word_phonemes_file_path) as inp_file:
            for line in tqdm.tqdm(inp_file, desc="Training"):
                data: Dict = orjson.loads(line)
                base_word: str = re.sub(r"\++", "", data["word"])
                if allowed_words and base_word not in allowed_words:
                    continue
                word = Word(word=data["word"], roots=set(data["roots"]))
                left_phonemes, right_phonemes = _get_phonemes_signatures(
                    data["phonemes"]
                )
                self._left_tree.add(left_phonemes, word)
                self._right_tree.add(right_phonemes, word)
                self._words.append(word)

    def save(self, out_file_path: str) -> None:
        with open(out_file_path, "wb") as out_file:
            pickle.dump(self, out_file)

    @staticmethod
    def load(file_path: Optional[str] = None) -> "Rhymer":
        file_path = file_path or _RHYMER_FILE_PATH
        with open(file_path, "rb") as inp_file:
            obj = pickle.load(inp_file)
            assert isinstance(obj, Rhymer)
            return obj

    def _get_rhymes(
        self,
        word: Word,
        min_n_matches: Tuple[int, int],
        max_n_skips: Tuple[int, int],
    ) -> List[Word]:
        phonemes: List[str] = _g2p.word_to_phonemes(word.word)
        left_phonemes, right_phonemes = _get_phonemes_signatures(phonemes)
        left_rhymes = self._left_tree.iterate_on_nodes(
            path=left_phonemes,
            min_n_matches=min_n_matches[0],
            max_n_skips=max_n_skips[0],
        )
        right_rhymes = self._right_tree.iterate_on_nodes(
            path=right_phonemes,
            min_n_matches=min_n_matches[1],
            max_n_skips=max_n_skips[1],
        )
        all_rhymes: Set[Word] = set(left_rhymes) & set(right_rhymes)

        rhymes: List[Word] = []
        for rhyme in all_rhymes:
            if rhyme.roots & word.roots:
                continue
            rhymes.append(rhyme)

        return rhymes

    def get_rhymes_by_scheme(
        self, scheme: List[str], n_attempts: int = 20
    ) -> List[Word]:
        rhymes: Optional[List[Word]] = None

        for _, params in zip(range(n_attempts), cycle(self._DEFAULT_PARAMS)):
            min_n_matches, max_n_skips = params
            rhymes = self.try_get_rhymes_by_scheme(
                scheme=scheme,
                min_n_matches=min_n_matches,
                max_n_skips=max_n_skips,
            )
            if rhymes is not None:
                break

        if rhymes is None:
            raise ValueError("Can't find enough rhymes. Try to increase n_attempts")

        return rhymes

    def try_get_rhymes_by_scheme(
        self,
        scheme: List[str],
        min_n_matches: Tuple[int, int],
        max_n_skips: Tuple[int, int],
    ) -> Optional[List[Word]]:
        code_to_words: Dict[str, List[Word]] = defaultdict(list)

        seen_roots: Set[str] = set()
        for code in scheme:
            words = code_to_words[code]
            if not words:
                word = random.choice(self._words)
                words.append(word)
                seen_roots |= word.roots
            else:
                prev_word = words[-1]
                prev_pos = _morph.parse(str(prev_word))[0].tag.POS
                rhymes = self._get_rhymes(prev_word, min_n_matches, max_n_skips)
                rhyme_found = False
                for word in rhymes:
                    if word.roots & seen_roots:
                        continue
                    pos = _morph.parse(str(word))[0].tag.POS
                    if pos == prev_pos:
                        continue
                    words.append(word)
                    seen_roots |= word.roots
                    rhyme_found = True
                    break
                if not rhyme_found:
                    return None

        rhymes: List[Word] = []
        for code in scheme:
            word = code_to_words[code].pop()
            rhymes.append(word)

        return rhymes

    def get_rhymes(self, seen_words: Sequence[Word]) -> List[Word]:
        rhymes: Set[Word] = set()
        word = seen_words[-1]
        prev_pos = _morph.parse(str(word))[0].tag.POS
        seen_roots = set(chain(*[w.roots for w in seen_words]))

        for params in self._DEFAULT_PARAMS:
            min_n_matches, max_n_skips = params
            for rhyme in self._get_rhymes(
                word=word,
                min_n_matches=min_n_matches,
                max_n_skips=max_n_skips,
            ):
                pos = _morph.parse(str(rhyme))[0].tag.POS
                if (rhyme.roots & seen_roots) or (pos == prev_pos):
                    continue
                rhymes.add(rhyme)
        return list(rhymes)


def _get_phonemes_signatures(phonemes: List[str]) -> Tuple[List[str], List[str]]:
    stress_idx: Optional[int] = None
    for stress_idx, phoneme in enumerate(phonemes):
        if phoneme in _STRESS_PHONEMES:
            break
    if stress_idx is None:
        raise ValueError(f"Stress phoneme is missed: {phonemes}")
    left = phonemes[: stress_idx + 1][::-1]
    right = phonemes[stress_idx:]
    return left, right
