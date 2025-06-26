FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml and other necessary files
COPY pyproject.toml ./

# Install dependencies for postgres
RUN apt-get update && \
    apt-get install -y libpq-dev gcc procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install .

# Create log directory
RUN mkdir -p /var/log && chmod 777 /var/log

# Copy the rest of the application code
COPY . .

EXPOSE 80

CMD ["sh", "-c", "alembic upgrade head && python main.py"]