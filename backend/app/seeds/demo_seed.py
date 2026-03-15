from app.core.bootstrap import bootstrap_demo_environment


def seed_demo_data() -> dict:
    summary = bootstrap_demo_environment()

    print("AegisCore demo bootstrap completed.")
    print(f"Database seeded: {summary['database_seeded']}")
    print(f"Anomaly model ready: {summary['anomaly_model_ready']}")

    if summary["database_counts"]:
        print("Persisted demo records:")
        for key, value in summary["database_counts"].items():
            print(f"  - {key}: {value}")

    return summary


if __name__ == "__main__":
    seed_demo_data()
