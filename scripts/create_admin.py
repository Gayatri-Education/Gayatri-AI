"""Create/promote an administrator using a private interactive password prompt."""

import argparse
import getpass
from sqlalchemy import select
from backend.database import Base, engine, SessionLocal
from backend.models import User
from backend.auth import password_hash
from backend.schemas import Register

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Admin password (10+ characters): ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    data = Register(email=args.email, name=args.name, password=password)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == data.email))
        if user:
            raise SystemExit(
                "Account already exists. No account was promoted or overwritten."
            )
        db.add(
            User(
                name=data.name,
                email=data.email,
                password_hash=password_hash(data.password),
                role="admin",
            )
        )
        db.commit()
    print("Administrator created. Sign in through the portal.")
