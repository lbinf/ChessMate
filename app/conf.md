# -----------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------
#
# Copy this file to .env and fill in your details.
# The application will prioritize these settings over the defaults
# in app/config.py.

# --- General Settings ---
FLASK_DEBUG=1
# LOG_LEVEL=DEBUG

# --- Database Settings ---

# Set to 'false' to disable the database entirely
DB_ENABLED=true

# Set the database type: 'mysql' or 'sqlite'
DB_TYPE=mysql

# --- Settings for MySQL (used if DB_TYPE is 'mysql') ---
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=chess_ai
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25

# --- Settings for SQLite (used if DB_TYPE is 'sqlite') ---
# Define the absolute or relative path for the SQLite database file.
# DB_PATH=./chess_helper.db