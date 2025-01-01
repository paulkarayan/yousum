import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import argparse
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI()

# Mount the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to check if a transcript already exists
def transcript_exists(slug):
    return os.path.exists(f"{slug}.pk")

# Helper to save transcript
def save_transcript(slug):
    transcript = YouTubeTranscriptApi.get_transcript(slug)
    transcript_text = "\n".join([entry["text"] for entry in transcript])
    file_path = f"{slug}.pk"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(transcript_text)
    return transcript_text

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logging.info(f"{request.method} {request.url} - Status: {response.status_code}")
    return response

@app.get("/ping")
async def ping():
    logging.debug("ping served")
    return {"message": "Pong"}

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Endpoint to process a YouTube transcript
@app.get("/process_transcript/{slug}")
async def process_transcript(slug, api_key="Nope"):
    try:
        # Check if the transcript already exists
        if transcript_exists(slug):
            with open(f"{slug}.pk", "r", encoding="utf-8") as file:
                transcript_text = file.read()
        else:
            # Fetch and save transcript
            transcript_text = save_transcript(slug)

        logging.info(transcript_text)
        if not api_key or api_key=="Nope":
            api_key = os.getenv("OPENAI_API_KEY")
            logging.info("used the free key")
        openai_client = OpenAI(api_key=api_key)

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                You are an information extraction service. Perform the following:
                STEP 0: Provide a SUMMARY of the content in 100 words or less.
                STEP 1: Extract the 5-10 most interesting FACTS:
                {transcript_text}
                """,
                }
            ],
            temperature=0.8,
            max_tokens=5000,
            top_p=0.8,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        result = response.choices[0].message.content

        logging.info(f"Processed transcript for slug: {slug}")
        logging.info(result)

        return {"output": result}

    except TranscriptsDisabled as e:
        logging.error(f"Transcripts are disabled for video: {slug}\n {e}")
        raise HTTPException(
            status_code=400, detail="Transcripts are disabled for this video."
        )
    except NoTranscriptFound:
        logging.error(f"No transcript found for video: {slug}")
        raise HTTPException(
            status_code=404, detail="No transcript found for this video."
        )
    except Exception as e:
        logging.error(f"Internal error processing video {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# CLI Support
def run_cli():
    parser = argparse.ArgumentParser(description="YouTube Transcript Processor")
    parser.add_argument(
        "slug",
        type=str,
        help="The YouTube video slug to process (e.g., fLVHISUAqLU)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="Your OpenAI API key",
    )
    args = parser.parse_args()

    try:
        # Fetch or reuse transcript
        if transcript_exists(args.slug):
            with open(f"{args.slug}.pk", "r", encoding="utf-8") as file:
                transcript_text = file.read()
        else:
            transcript_text = save_transcript(args.slug)

        # Use the provided OpenAI API key
        openai_client = OpenAI(api_key=args.api_key)

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                You are an information extraction service. Perform the following:
                STEP 0: Provide a SUMMARY of the content in 100 words or less.
                STEP 1: Extract the 5-10 most interesting FACTS:
                {transcript_text}
                """,
                }
            ],
            temperature=0.8,
            max_tokens=5000,
            top_p=0.8,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        result = response.choices[0].message.content

        logging.info(f"Processed transcript for CLI slug: {args.slug}")
        logging.info(result)
        return {"output": result}

    except TranscriptsDisabled:
        logging.error(f"CLI: Transcripts are disabled for video: {args.slug}")
        print("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        logging.error(f"CLI: No transcript found for video: {args.slug}")
        print("No transcript found for this video.")
    except Exception as e:
        logging.error(f"CLI: An error occurred for video {args.slug}: {str(e)}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import sys

    # Run as CLI if executed directly
    if len(sys.argv) > 1:
        run_cli()
