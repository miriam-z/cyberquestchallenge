FROM python:3.12

# Create a non-root user and switch to it
RUN useradd -m -u 10001 appuser

USER appuser

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY --chown=appuser:appuser . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

CMD ["chainlit", "run", "app.py", "-h", "-w", "--host", "0.0.0.0" ,"--port", "7860"]