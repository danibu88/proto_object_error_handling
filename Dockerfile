FROM python:3.12-slim

# Install locales and configure them properly
RUN apt-get update && \
    apt-get install -y locales libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/* && \
    echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=de_DE.UTF-8

# Set environment variables for locale
ENV LANG=de_DE.UTF-8 \
    LANGUAGE=de_DE:de \
    LC_ALL=de_DE.UTF-8

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY door_service ./door_service
COPY alembic.ini .
COPY alembic ./alembic
COPY .streamlit ./.streamlit

COPY setup.py .
RUN pip install -e .

# Copy start script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# Streamlit runs on 8501 by default
EXPOSE 8501

CMD ["./start.sh"]
