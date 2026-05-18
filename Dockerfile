FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    psutil==7.0.0 \
    sqlalchemy==2.0.36 \
    pymysql==1.1.1

COPY agent.py .

CMD ["python", "agent.py"]
