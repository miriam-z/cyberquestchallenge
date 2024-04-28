FROM python:3.12

# Create a non-root user and switch to it
RUN useradd -m -u 15000 user

USER 15000

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory in the container
WORKDIR $HOME/app

COPY --chown=user . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# RUN --mount=type=secret,id=HUGGINGFACE_API_TOKEN,mode=0444,required=true 

# Make port 8000 available to the world outside this container
EXPOSE 7860

CMD ["chainlit", "run", "app.py", "-h", "-w", "--host", "0.0.0.0" ,"--port", "7860"]