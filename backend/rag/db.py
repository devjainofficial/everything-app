"""db.py — the one place that knows how to reach the Supabase Postgres (pgvector) DB."""
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()  # read project-root .env into os.environ (SUPABASE_DB_URL lives there)


def get_conn():
    """Open a new connection to the database. Caller is responsible for closing/committing."""
    # connect_timeout guards against hanging if the pooler is unreachable.
    return psycopg.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=20)
