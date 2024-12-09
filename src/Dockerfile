ARG APP_PATH=/app

FROM python:3.9-bullseye as pragya-image

ARG APP_PATH

COPY requirements.txt /tmp/

RUN apt-get update -y

RUN python -m pip install --upgrade pip setuptools wheel \
        && pip install -r /tmp/requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader stopwords \
&& python -m nltk.downloader wordnet \
&& python -m nltk.downloader punkt \
&& cp -r /root/nltk_data /usr/local/share/nltk_data

ENV http_proxy= \
    https_proxy= \
    no_proxy=

WORKDIR $APP_PATH
COPY . $APP_PATH

CMD ["gunicorn", "-c", "config.py", "main:app"]
