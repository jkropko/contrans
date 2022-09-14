FROM python:3.10.7-bullseye

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY 

WORKDIR /contrans

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root"]