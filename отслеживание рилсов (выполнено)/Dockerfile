FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код и картинки (папка images может быть пустой — положите файлы перед деплоем)
COPY bot.py .
COPY images ./images

CMD ["python", "bot.py"]
