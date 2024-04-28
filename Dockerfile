FROM python:3.12

RUN useradd -m -u 10001 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

COPY ./requirements.txt ~/app/requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["chainlit", "run", "app.py", "--port", "7860"]