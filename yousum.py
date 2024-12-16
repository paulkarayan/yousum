import openai
import ast
import argparse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def save_transcript_to_file(slug):
    """
    Fetches the transcript of a YouTube video using the provided slug
    and saves it to a .pk file.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(slug)
        
        transcript_text = "\n".join([entry['text'] for entry in transcript])
        
        file_name = f"{slug}.pk"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(transcript_text)
        
        print(f"Transcript saved to {file_name}")
    
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for the video with slug: {slug}")
    except NoTranscriptFound:
        print(f"No transcript found for the video with slug: {slug}")
    except Exception as e:
        print(f"An error occurred while saving the transcript: {e}")


def describe_transcript_with_llm(content):
    """
    Uses OpenAI's GPT to generate a summary and extract facts from the transcript content.
    """
    try:
        prep = f"""
        You are an information extraction service for text content.
        Perform 2 distinct steps for the input:

        STEP
        0. Extract a summary of the content in 100 words or less, into a section called SUMMARY.
        1. Extract the 5-10 most interesting ideas and facts into a section called FACTS:.

        Do not start items with the same opening words.
        {content}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": prep,
                },
            ],
            temperature=0.7,
            max_tokens=6000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        description = response.choices[0].message.content
        return description

    except Exception as e:
        print(f"Error during transcript processing: {e}")
        return None


def read_and_convert_data(file_path):
    """
    Reads a file and converts its content into a Python structure using `ast.literal_eval`.
    """
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
            return ast.literal_eval(file_content)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except (SyntaxError, ValueError) as e:
        print(f"Error processing the file {file_path}: {e}")
        return None


def extract_text_to_paragraph(data):
    """
    Converts a list of transcript entries into a single paragraph of text.
    """
    return " ".join(item["text"] for sublist in data for item in sublist)


def prime_the_data(file_path="output.txt"):
    """
    Reads the transcript data from a file and converts it into a paragraph of text.
    """
    data = read_and_convert_data(file_path)
    if data is not None:
        return extract_text_to_paragraph(data)
    else:
        print("Failed to load data.")
        return None


def main():
    parser = argparse.ArgumentParser(description="Process a YouTube video")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command to save the transcript
    save_parser = subparsers.add_parser("save", help="Save a transcript to a file")
    save_parser.add_argument(
        "slug", type=str, help="The YouTube video slug to save the transcript for"
    )

    # Command to process a transcript file
    process_parser = subparsers.add_parser("process", help="Process a transcript file")
    process_parser.add_argument(
        "file_path",
        nargs="?",
        default="CO-6iqCum1w.pk",
        type=str,
        help="The YouTube video transcript file to process",
    )

    args = parser.parse_args()

    if args.command == "save":
        # Save the transcript directly
        save_transcript_to_file(args.slug)
    elif args.command == "process":
        # Process the transcript file
        transcript = prime_the_data(args.file_path)
        if transcript:
            output = describe_transcript_with_llm(transcript)
            if output:
                print(output)
    else:
        parser.print_help()


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

        # Process transcript with OpenAI (e.g., summarize and extract facts)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
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
            temperature=0.7,
            max_tokens=600,
        )
        result = response.choices[0].message.content

        return {"output": result}

    except TranscriptsDisabled:
        raise HTTPException(status_code=400, detail="Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found for this video.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    main()
