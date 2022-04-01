FROM python:3

WORKDIR /usr/src/app

# Prepare App
COPY app.py . 
COPY requirements.txt . 
RUN pip install -r requirements.txt && rm requirements.txt

CMD python app.py
