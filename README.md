# Competitor Monitoring Assistant (Desktop)

Приложение для анализа сайтов, изображений и PDF: выявляет сильные и слабые стороны и даёт рекомендации.
Десктоп‑версия приложения на PyQt6. Проект автономен и содержит встроенный FastAPI‑бекенд.

## Возможности

- Анализ текста конкурента
- Анализ изображения
- OCR PDF
- Демо‑парсинг страницы по URL

## Требования

- Python 3.10+
- macOS для сборки `.app`/`.dmg`
- Google Chrome (для демо‑парсинга через Selenium)

## Установка

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Создайте `.env` в этой папке (можно на базе `.env.example`).

## Переменные окружения

Основные:

- `GIGACHAT_CLIENT_ID`
- `GIGACHAT_CLIENT_SECRET`
- `GIGACHAT_MODEL` (по умолчанию `GigaChat`)
- `GIGACHAT_CA_CERT` (путь к корневому сертификату)
- `GIGACHAT_SKIP_VERIFY` (`true/false`)

Yandex Cloud (опционально, для связанных сервисов):

- `YC_API_KEY`
- `YC_FOLDER_ID`
- `YC_ART_MODEL_URI`
- `YC_SKIP_VERIFY` (`true/false`)

Selenium:

- `CHROME_DRIVER_PATH` (опционально, если драйвер не находится автоматически)

Если ключи не заданы, приложение использует встроенные fallback‑ответы.

## Запуск

```
python main.py
```

## Сборка .app и .dmg (macOS)

```
chmod +x build_app.sh build_dmg.sh
./build_app.sh
./build_dmg.sh
```

Результаты сборки:
- `.app`: `dist/CompetitorMonitoring.app`
- `.dmg`: `dist/CompetitorMonitoring.dmg`

## Примечания по запуску на macOS

Неподписанные приложения могут блокироваться Gatekeeper. Для локального запуска
используйте «Открыть» из контекстного меню или разрешите запуск в
`System Settings → Privacy & Security`.
