FROM python:3.10
WORKDIR /app
COPY . .
RUN apt update && apt upgrade -y
RUN pip install -r requirements.txt
CMD ["python", "bot.py", "-t", "/secret/token"]
