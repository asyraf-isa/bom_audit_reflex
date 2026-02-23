import reflex as rx
import os
from dotenv import load_dotenv

# This loads the variables from a .env file (for local testing)
load_dotenv()

config = rx.Config(
    app_name="bom_audit_reflex",
    # 1. Get the URL from environment, or 2. Use local sqlite as backup
    db_url=os.getenv("DATABASE_URL", "sqlite:///bom_audit.db"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)