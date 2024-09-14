FROM python:3-alpine3.15
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies needed to build psycopg2
RUN apk update && apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev

# Set the working directory
WORKDIR /app

# Copy only the requirements.txt first
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application files
COPY . .

# Expose port 4000
EXPOSE 4000

# Specify the command to run on container startup
 CMD ["gunicorn", "--bind", "0.0.0.0:4000", "-w", "4", "--log-level", "debug", "app:app"]
#CMD ["python", "app.py"]
