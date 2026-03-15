from app.db.init_db import init_db


def seed_demo_data() -> None:
    init_db()
    print("AegisCore demo seed scaffold completed.")
    print("Next step: insert sample users, alerts, incidents, and integration metadata.")


if __name__ == "__main__":
    seed_demo_data()
