FROM python:3.12
WORKDIR /app
COPY src src
COPY requirements.txt .
COPY config.json .
RUN apt update && apt upgrade -y
RUN pip install -r requirements.txt
CMD ["python", "src/start_bot.py"]
