FROM python:3.12

RUN useradd -m -u 15000 user

USER 15000

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

# Create a writable directory for the application
# RUN mkdir -p /app/.files
RUN chown -R user:user /app/.files

RUN chmod 750 /app/.files/

COPY ./requirements.txt ~/app/requirements.txt

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]

