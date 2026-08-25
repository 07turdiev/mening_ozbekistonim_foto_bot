FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ma'lumotlar host bilan mount qilinadi (contest.db, uploads/, exports/)
CMD ["python", "bot.py"]
