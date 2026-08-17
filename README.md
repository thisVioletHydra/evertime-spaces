# Evertime Spaces

Часы для macOS на всех рабочих столах (Spaces): время в правом верхнем углу, когда системные часы спрятаны (фуллскрин, автоскрытие менюбара). Когда менюбар снова виден — оверлей прячется, чтобы не дублировать системные часы.

## Требования

- macOS 13+
- Python 3.10+

## Установка

```bash
git clone git@github.com:thisVioletHydra/evertime-spaces.git
cd evertime-spaces
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Запуск из терминала

```bash
./run.sh
```

Или:

```bash
.venv/bin/python evertime.py
```

`Ctrl+C` останавливает процесс.

## Запуск как обычное приложение

```text
~/Applications/Evertime Spaces.app
```

```bash
open ~/Applications/Evertime\ Spaces.app
```

Автозапуск: **Системные настройки → Основные → Объекты входа** → добавь **Evertime Spaces**.

В Dock не светится (`LSUIElement`) — это фоновый оверлей.

> `.app` запускает `.venv/bin/python evertime.py` из клона репо. Не переноси папку проекта без правки лаунчера внутри `.app`.

## Как это устроено

- прозрачная `NSPanel` поверх окон и фуллскрин-спейсов
- показ только когда виджеты системного менюбара не видны
- цвет текста — приглушённый серый

## Лицензия

MIT
