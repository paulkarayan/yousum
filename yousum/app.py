from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import argparse

app = FastAPI()

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

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

# Endpoint to process a YouTube transcript
@app.get("/process_transcript/{slug}")
async def process_transcript(slug: str):
    try:
        # Check if the transcript already exists
        if transcript_exists(slug):
            with open(f"{slug}.pk", "r", encoding="utf-8") as file:
                transcript_text = file.read()
        else:
            # Fetch and save transcript
            transcript_text = save_transcript(slug)
        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        # Process transcript with OpenAI (e.g., summarize and extract facts)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"""
                You are an information extraction service. Perform the following:
                STEP 0: Provide a SUMMARY of the content in 100 words or less.
                STEP 1: Extract the 5-10 most interesting FACTS:
                {transcript_text}
                """,}],
            temperature=0.8,
            max_tokens=5000,
            top_p=0.8,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        result = response.choices[0].message.content

        return {"output": result}

    except TranscriptsDisabled:
        raise HTTPException(status_code=400, detail="Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found for this video.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# CLI Support
def run_cli():
    parser = argparse.ArgumentParser(description="YouTube Transcript Processor")
    parser.add_argument(
        "slug",
        type=str,
        help="The YouTube video slug to process (e.g., fLVHISUAqLU)",
    )
    args = parser.parse_args()

    try:
        # Fetch or reuse transcript
        if transcript_exists(args.slug):
            with open(f"{args.slug}.pk", "r", encoding="utf-8") as file:
                transcript_text = file.read()
        else:
            transcript_text = save_transcript(args.slug)

            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"""
                    You are an information extraction service. Perform the following:
                    STEP 0: Provide a SUMMARY of the content in 100 words or less.
                    STEP 1: Extract the 5-10 most interesting FACTS:
                    {transcript_text}
                    """,}],
                temperature=0.8,
                max_tokens=5000,
                top_p=0.8,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )

            result = response.choices[0].message.content
            print(result)

    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        print("No transcript found for this video.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import sys

    # Run as CLI if executed directly
    if len(sys.argv) > 1:
        run_cli()
