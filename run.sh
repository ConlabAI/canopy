# Load environment variables from .env file and export them
set -a # automatically export all variables
source .env
set +a # stop automatically exporting

# Existing command
uvicorn canopy_server.app:app --host localhost --port 8000 --reload