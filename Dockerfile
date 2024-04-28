FROM python:3.12

# Set the working directory in the container
WORKDIR /app

RUN useradd -m -u 15000 user

USER 15000

COPY app.py app.py

COPY --chown=15000 . .

RUN pip install --no-cache-dir -r requirements.txt

# do not change the arguments
ENTRYPOINT ["chainlit", "run", "app.py", "--host=0.0.0.0", "--port=80", "--headless"]