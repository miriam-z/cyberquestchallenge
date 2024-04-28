FROM python:3.12

RUN useradd -m -u 15000 user

USER 15000

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

# Create a writable directory for the application
RUN mkdir -p $HOME/app/.files

RUN chown -R user:user $HOME/app/.files

RUN chmod 777 $HOME/app/.files/


COPY ./requirements.txt ~/app/requirements.txt

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]

# OSError: [Errno 30] Read-only file system: '/home/user/app/.files'
# [Errno 30] Read-only file system: '/home/user/app/.files/f78018c1-8331-4ddc-a3e7-b3e56673306a'