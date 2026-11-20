import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def get_json(url: str):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body)


def main():
    parser = argparse.ArgumentParser(description="GitGuru live smoke test")
    parser.add_argument("base_url")
    parser.add_argument("--expect-version")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    health_url = f"{base_url}/health"

    # Wait for the expected deployment version.
    for attempt in range(30):
        try:
            status, health = get_json(health_url)
            version = health.get("version")

            if status == 200 and (
                not args.expect_version or version == args.expect_version
            ):
                print(f"ok   /health -> {status}, version {version}")
                break

            print(f"waiting: {health_url} -> {version}")

        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"waiting: {health_url} -> {error}")

        time.sleep(10)
    else:
        print("FAIL /health: expected version was not available")
        sys.exit(1)

    # Check database readiness.
    try:
        status, ready = get_json(f"{base_url}/ready")

        if status != 200 or ready.get("status") != "ready":
            raise RuntimeError(f"Unexpected readiness response: {ready}")

        print(f"ok   /ready -> {status} {ready}")

    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        RuntimeError,
    ) as error:
        print(f"FAIL /ready -> {error}")
        sys.exit(1)

    # Check the documents API.
    try:
        status, _documents = get_json(f"{base_url}/v1/documents?limit=1")

        if status != 200:
            raise RuntimeError(f"Unexpected HTTP status: {status}")

        print(f"ok   /v1/documents?limit=1 -> {status}")

    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        RuntimeError,
    ) as error:
        print(f"FAIL /v1/documents?limit=1 -> {error}")
        sys.exit(1)

    print("Smoke test passed")


if __name__ == "__main__":
    main()
