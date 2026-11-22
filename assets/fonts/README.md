# Шрифты (офлайн, в репозитории)

Игра работает **без интернета**: все шрифты лежат прямо здесь и подключаются
по относительному пути. Скачивать ничего не нужно.

## Что лежит и зачем

| Файл | Размер | Лицензия | Зачем |
|---|---|---|---|
| `JetBrainsMono-Regular/Bold/Medium.ttf` | 264–268 КБ | SIL OFL 1.1 (`JetBrainsMono-OFL.txt`) | **Основной** шрифт: терминальный моноширинный вид, как в старом tkinter-интерфейсе |
| `OpenMoji-black-glyf.ttf` | 1.4 МБ | CC BY-SA 4.0 (`OpenMoji-LICENSE.txt`) | **Эмодзи** (монохромный line-art): 💵 🎉 🔐 💣 🧮 ⚡ ⚠ 💀 🖥 📜 ⚙ ✂ 💾 👤 🐱 |
| `NotoSansSymbols2-Regular.ttf` | 641 КБ | SIL OFL 1.1 (`Noto-LICENSE.txt`) | Запасные символы: стрелки, геометрия, ⏱ ⌨ ↩ |
| `NotoSansMono-Regular/Bold.ttf` | 501–513 КБ | SIL OFL 1.1 | Альтернативный моноширинный (кириллица + псевдографика) |
| `NotoSans-Regular/Bold.ttf` | 556–562 КБ | SIL OFL 1.1 | Пропорциональный — для заголовков/кнопок, если понадобится |
| `IBMPlexMono-Regular/Bold.ttf` | 169–171 КБ | SIL OFL 1.1 (`IBMPlex-OFL.txt`) | Ещё один «ламповый» моноширинный на выбор |

⚠️ **Важно:** ни один шрифт не покрывает всё. Например JetBrains Mono не
содержит эмодзи, а OpenMoji не содержит кириллицу. Поэтому рендер идёт
**цепочкой с фолбэком по глифам** — см. `fontloader.py`.

## Как пользоваться

```python
import pygame
from assets.fonts.fontloader import FontBook

pygame.init()
book = FontBook(pygame)

# строка с миксом: кириллица + псевдографика + эмодзи
surf = book.render('◆ Взломано 3 ⏱ 25 сек 💵 $1234', 20, (0, 255, 0))
screen.blit(surf, (20, 20))
```

`FontBook` сам разбирает `cmap` шрифтов (без `fontTools`) и для каждого символа
берёт первый шрифт из цепочки, где глиф есть. Цепочка по умолчанию:

```
jetbrains → symbols → emoji
```

Невидимые символы (`U+FE0F` в «✂️» и т.п.) отфильтровываются — иначе pygame
падает с `Text has zero width`.

## Проверка покрытия

```bash
python3 assets/fonts/fontloader.py     # рендерит демо-картинку
```

Покрытие символов, которые реально встречаются в `legacy/hacker-app.py`:

| Цепочка | Покрытие |
|---|---|
| JetBrains Mono | 71.3% |
| JetBrains Mono + OpenMoji | **100%** |

## Лицензии

Все шрифты распространяются по свободным лицензиям, текст которых лежит рядом:

- SIL Open Font License 1.1 — `JetBrainsMono-OFL.txt`, `Noto-LICENSE.txt`, `IBMPlex-OFL.txt`
- CC BY-SA 4.0 — `OpenMoji-LICENSE.txt`

При распространении игры сохраните эти файлы и укажите авторов шрифтов:

- **JetBrains Mono** — JetBrains, https://github.com/JetBrains/JetBrainsMono
- **OpenMoji** — OpenMoji project (HfG Schwäbisch Gmünd), https://openmoji.org
- **Noto Sans / Noto Sans Mono / Noto Sans Symbols 2** — Google, https://github.com/notofonts/noto-fonts
- **IBM Plex Mono** — IBM, https://github.com/IBM/plex
