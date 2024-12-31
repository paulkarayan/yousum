import pytest
import os
from yousum.app import transcript_exists, save_transcript

from fastapi.testclient import TestClient
from yousum.app import app

client = TestClient(app)

# Test slugs
WORKING_SLUG = "fLVHISUAqLU"  # Replace with a known working slug
NON_WORKING_SLUG = "AK9rfbJzys"  # Replace with a known non-working slug


# Test the transcript_exists function
def test_transcript_exists():
    # Create a dummy file for testing
    dummy_slug = "dummy_slug"
    dummy_file = f"{dummy_slug}.pk"
    with open(dummy_file, "w") as file:
        file.write("Test content")

    assert transcript_exists(dummy_slug) is True
    os.remove(dummy_file)
    assert transcript_exists(dummy_slug) is False


# Test saving a transcript (mocked for the working slug)
def test_save_transcript():
    if os.path.exists(f"{WORKING_SLUG}.pk"):
        os.remove(f"{WORKING_SLUG}.pk")

    try:
        transcript = save_transcript(WORKING_SLUG)
        assert os.path.exists(f"{WORKING_SLUG}.pk") is True
        assert len(transcript) > 0
    except Exception as e:
        pytest.fail(f"Saving transcript failed: {e}")


# Test the FastAPI endpoint for a working slug
def test_process_transcript_working():
    response = client.get(f"/process_transcript/{WORKING_SLUG}")
    assert response.status_code == 200
    assert "output" in response.json()


# Test the FastAPI endpoint for a non-working slug
def test_process_transcript_non_working():
    response = client.get(f"/process_transcript/{NON_WORKING_SLUG}")
    assert response.status_code == 404
    assert response.json()["detail"] == "No transcript found for this video."


# Test the CLI directly
def test_cli():
    import subprocess

    # Run the CLI for the working slug
    result = subprocess.run(
        ["python", "app.py", WORKING_SLUG],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert "SUMMARY" in result.stdout.decode()

    # Run the CLI for the non-working slug
    result = subprocess.run(
        ["python", "app.py", NON_WORKING_SLUG],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert "No transcript found for this video" in result.stdout.decode()
