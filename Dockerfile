FROM python:3.7.3-slim

RUN apt update

RUN mkdir /web

WORKDIR /root

ADD requirements.txt /web/requirements.txt
RUN python -m pip install -r /web/requirements.txt --no-cache-dir

WORKDIR /web

ADD . /web

ENV PORT 5000

CMD ["python","initialize.py","&&","gunicorn", "-b","0.0.0.0:$PORT","gavel:app","-w","3"]
