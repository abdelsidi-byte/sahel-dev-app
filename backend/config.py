# Sahel Dev Database Configuration
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./sahel_dev.db"  # Local SQLite for development
)

# For production with PostgreSQL (Neon):
# DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"