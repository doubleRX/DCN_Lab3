FROM python:3.11-slim

WORKDIR /app

COPY server.py records.json ./

EXPOSE 53533/udp

CMD ["python", "server.py"]
