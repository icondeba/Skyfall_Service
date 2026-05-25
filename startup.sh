#!/bin/bash
set -e

# Install Microsoft ODBC Driver 18 for SQL Server (required for pyodbc on Linux)
if [ ! -f /etc/apt/sources.list.d/mssql-release.list ]; then
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl -sSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
    apt-get update -qq
    ACCEPT_EULA=Y apt-get install -y -q msodbcsql18 unixodbc-dev
fi

# Start the FastAPI app
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --timeout 120
