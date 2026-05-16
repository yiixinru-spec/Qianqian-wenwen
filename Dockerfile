FROM python:3.10-slim

WORKDIR /app
COPY . /app

ENV HOST=0.0.0.0
ENV PORT=7860

EXPOSE 7860

CMD ["python", "server.py"]
