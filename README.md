Door Service Assistant

A Streamlit based self service application for diagnosing and handling door related errors and incidents.

The app guides users through a troubleshooting flow for door systems, supports error code based diagnosis, offers chat assisted help, and includes analytics and ticketing views. It is designed to run locally or in Docker with a PostgreSQL database and Alembic migrations.

**Features**
Interactive troubleshooting workflow for door issues
Error code based diagnosis
Streamlit user interface
Chat integration for guided assistance
Ticketing and analytics views
PostgreSQL backed persistence
Alembic database migrations
Docker and Docker Compose setup for local and deployed environments

**Project structure**
proto_object_error_handling/
├── app/                         # main application package
│   ├── __init__.py
│   ├── main.py                  # (formerly app.py)
│
│   ├── domain/                  # core logic
│   │   ├── exceptions.py
│   │   ├── navigator.py
│   │   └── validators.py
│
│   ├── infrastructure/          # technical concerns
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── operations.py
│   │   └── config/
│
│   ├── interface/               # UI / interaction
│   │   ├── analytics.py
│   │   ├── chat.py
│   │   ├── components.py
│   │   └── ticketing.py
│
│   └── resources/               # static data
│       ├── dps.jpg
│       └── troubleshooting.json
│
├── alembic/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.local.yml
│   └── docker-compose.streamlit.yml
│
├── requirements.txt
├── setup.py
└── start.sh

**How it works**

The application loads a troubleshooting tree from service/data/troubleshooting.json and uses a navigator component to move the user through decision nodes, action nodes, and resolution steps.

**Typical flow:**

Identify the door or issue
Enter or select an error code if available
Follow troubleshooting steps
Review suggested actions or resolution
Escalate through ticketing or chat support if needed

**Tech stack**
Python 3.8+
Streamlit
PostgreSQL
SQLAlchemy
Alembic
Docker
Docker Compose

**Requirements**
Install dependencies with:

pip install -r requirements.txt

**Main dependencies include:**

streamlit
streamlit-qrcode-scanner
pandas
numpy
python-dotenv
sqlalchemy
alembic
psycopg2-binary
aiohttp

**Environment variables**

Create a .env file based on .env.example.

Example:

POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

ADMIN_PASSWORD=your_admin_password
CHAT_API_URL=https://your-chat-api
CHAT_EXPERT_ID=your_expert_id
Local development
Option 1: Run with Docker Compose
docker compose -f docker-compose.local.yml up --build

This starts:

the Streamlit app on port 8501
a PostgreSQL database
automatic Alembic migrations during startup

Open the app at:

http://localhost:8501

Option 2: Run manually
Create and activate a virtual environment
Install dependencies
Set environment variables
Start PostgreSQL
Run migrations
Start Streamlit

Example:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
streamlit run service/app.py

**Deployment**

A second compose file, docker-compose.streamlit.yml, is included for deployment scenarios with reverse proxy related environment variables such as:

VIRTUAL_HOST
VIRTUAL_PORT
LETSENCRYPT_HOST
LETSENCRYPT_EMAIL

This setup appears intended for proxy based hosting with persistent PostgreSQL storage.

**Database**

The project uses PostgreSQL together with Alembic migrations.

On container startup, start.sh:

waits for the database to become available
runs alembic upgrade head
starts the Streamlit app
Validation and navigation

The application includes validators for:

door serial numbers
door types
error codes
service ticket contact data

The navigation logic is implemented as a tree based workflow that tracks user choices and supports backward navigation.

**Notes**
The UI text is primarily in German.
Locale settings are configured for de_DE.UTF-8.
The application currently appears focused on sliding door self diagnosis.
Known point to verify

Before production use, verify the package path naming in the Docker build:

setup.py references service.app:main
Dockerfile copies door_service

If the app package is indeed service, the Dockerfile may need to be adjusted.

**License**

This project is licensed under the MIT License.

This repository is provided as a research prototype and is not associated with any specific company or production system.

**Contributing**
Contributions are welcome. Please open an issue or submit a pull request for bug fixes, improvements, or documentation updates.
