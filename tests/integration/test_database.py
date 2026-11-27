import json
import os
import subprocess
import sys


def test_loader_is_idempotent(database_url, tmp_path):
    data = tmp_path / "records.json"
    data.write_text(
        json.dumps([{"id": "L1", "x": 1}, {"id": "L2", "x": 2}]),
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "APP_ENV": "ci",
        "DATABASE_URL": database_url,
        "DATA_FILE": str(data),
    }

    def run() -> str:
        cmd = [sys.executable, "scripts/load_db.py"]

        result = subprocess.run(
            cmd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        if result.returncode != 0:
            raise RuntimeError("Loader failed")

        return result.stdout

    assert "inserted=2" in run()
    assert "inserted=0 updated=0 unchanged=2" in run()
