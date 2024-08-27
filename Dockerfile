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

# Copy the local directory contents into the container at /app
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 4000
EXPOSE 4000

# Specify the command to run on container startup
CMD ["gunicorn", "--bind", "0.0.0.0:4000", "-w", "4", "app:app"]
