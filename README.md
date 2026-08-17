# Evertime

Минимальные часы для macOS: время в правом верхнем углу, когда системные часы спрятаны (фуллскрин, автоскрытие менюбара). Когда менюбар снова виден — оверлей прячется, чтобы не дублировать системные часы.

## Требования

- macOS
- Python 3.10+

## Установка

```bash
git clone git@github.com:thisVioletHydra/corner-timer.git
cd corner-timer
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Запуск

```bash
./run.sh
```

Или напрямую:

```bash
.venv/bin/python evertime.py
```

`Ctrl+C` в терминале останавливает процесс.

## Автозапуск (launchd)

Чтобы крутилось в фоне без терминала:

```bash
cat > ~/Library/LaunchAgents/com.evertime.app.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.evertime.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>/ABSOLUTE/PATH/TO/corner-timer/.venv/bin/python</string>
        <string>/ABSOLUTE/PATH/TO/corner-timer/evertime.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/ABSOLUTE/PATH/TO/corner-timer</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>StandardErrorPath</key>
    <string>/tmp/evertime.err</string>
</dict>
</plist>
EOF

# подставь свой путь вместо /ABSOLUTE/PATH/TO/corner-timer
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.evertime.app.plist
```

Остановить:

```bash
launchctl bootout gui/$(id -u)/com.evertime.app
```

## Как это устроено

- прозрачная `NSPanel` поверх окон и фуллскрин-спейсов
- показ только когда виджеты системного менюбара (часы/Wi‑Fi и т.п.) не видны
- цвет текста — приглушённый серый

## Лицензия

MIT
