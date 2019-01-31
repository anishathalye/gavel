FROM python:3.6
ADD . /code
WORKDIR /code

RUN apt-get update -qqy && apt-get install -qqy libopenblas-dev gfortran
RUN apt-get install -y make automake g++ subversion python3-dev
RUN apt-get install -y gcc musl-dev postgresql
RUN python -m pip install -r requirements.txt --no-cache-dir
RUN python initialize.py
CMD ["python", "./runserver.py"]
