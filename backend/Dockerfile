FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip

RUN pip install gunicorn==20.1.0

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

COPY foodgram/data .

WORKDIR /app/foodgram

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]