FROM python:3.9

COPY . /workdir/
WORKDIR /workdir/

RUN pip install --user flask
RUN pip install --user flask_cors
RUN pip install --user firebase-admin==4.5.2
RUN pip install --user mysql-connector-python

CMD ["python3","-u","app.py", "dev"]
