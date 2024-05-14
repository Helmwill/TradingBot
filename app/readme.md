# Project App

This Django project is designed to provide an API that includes a health status route to monitor the application's status. This README covers the setup, configuration, and running of the project to ensure the health status route is operational.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or later
- pip (Python package installer)

## Setting Up the Environment

1. **Clone the Repository**

   Start by cloning the project repository to your local machine:

   ```bash
   git clone https://your-repository-url.git
   cd project-app

2. **Create and activate environment**

    Create a virtual environment to isolate package dependencies:

    python -a venv venv

    activate the virtual environment in windows:
    venv\scripts\activate

    actviate the virtual environment in unix/mac:
    source /venv/bin/activate
 
3. **Configure Environment Variables**
    Configure your application settings using an environment file (.env). 
    If you don’t already have a `.env` file, 
    create one in your project root directory:
    On Unix or MacOS:
    touch .env
    On windows:
    type nul > .env

    Edit the `.env` file to add necessary configurations:
    DEBUG=TRUE
    SECRET_KEY=your_secret_key_here
    ALLOWED_HOSTS=localhost0,127.0.0.1

    Ensure your Django settings are configured to read from the `.env` 
    file using a library like `django-environ`.

4. **Run migrations**

    python manage.py migrate

5. **Start the development server**

    python manage.py runserver

    Visit `http://127.0.0.1:8000/health/` in your browser to see the health status message.
    

