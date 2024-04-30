FROM python:3.7

ENV PYTHONUNBUFFERED=1

WORKDIR /app


COPY requirements.txt .
RUN pip --proxy http://proxy1.emirates.net.ae:8080 install requests
RUN pip --proxy http://proxy1.emirates.net.ae:8080 install -r requirements.txt

Copy  . .  

EXPOSE 5011

ENV DEBUG=0
ENV MONGO_HOST_CEQ="mongodb://thedash:dash1234@vm-360-mongo2:27017/ceq?replicaSet=rs0"

CMD [ "gunicorn", "--bind", "0.0.0.0:5011", "--workers", "2", "wsgi:app" ]

