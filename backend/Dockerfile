FROM python:3.9

COPY . /workdir/
WORKDIR /workdir/

RUN pip install --upgrade pip

RUN pip install --user flask
RUN pip install --user flask_cors
RUN pip install --user firebase-admin==4.5.2
RUN pip install --user mysql-connector-python
RUN pip install --user flask-restx

ENV TZ=Europe/Prague

CMD ["python3","-u","app.py", "prod"]
