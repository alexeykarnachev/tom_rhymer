# TOM RHYMER
Library for Russian imprecise rhymes generation.

## Quick Start
Generate rhymes by any given rhyme scheme (`aabb`, `abab`, `aaccbb`, etc ...):
```python
from tom_rhymer.rhymer import Rhymer

rhymer = Rhymer.load()
for rhyme in rhymer.get_rhymes_by_scheme('abab'):
    print(str(rhyme))

# предоставленными
# отличите
# доставлена
# ограничительных
```
Generate rhymes word by word:
```python
import random

from tom_rhymer.rhymer import Rhymer

rhymer = Rhymer.load()

word = random.choice(rhymer.words)
seen_words = [word]
for _ in range(8):
    rhymes = rhymer.get_rhymes(seen_words)
    rhyme = random.choice(rhymes)
    seen_words.append(rhyme)

for word in seen_words:
    print(str(word))

# матриархату
# сохатому
# патриархаты
# ухохатывались
# блатхатам
# двухатомные
# олигархат
# горбатых
# вырабатываю
```
