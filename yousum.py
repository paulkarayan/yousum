import openai
import ast
import argparse


def describe_transcript_with_llm(content):
    try:
        # summarize the youtube transcript here:
        prep = f"""
        You are a information extraction service for text content.
        You perform 2 separate and distinct steps for the input:

        STEP
        0. you extract a summary of the content in 100 words or less, into a section called SUMMARY
        1. you extract the 5-10 most interesting ideas and facts into a section called FACTS:.

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

        description = list(response.choices)[0]
        description.to_dict()
        # pprint.pprint(description['message']['content'])

        return description["message"]["content"]

    except Exception as e:
        print(e)


# Function to read data from a file and convert it to a Python structure
def read_and_convert_data(file_path):
    try:
        with open(file_path, "r") as file:
            # Read the entire content of the file
            file_content = file.read()
            # Convert the string to a Python structure
            return ast.literal_eval(file_content)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except (SyntaxError, ValueError) as e:
        print(f"Error processing the file {file_path}: {e}")
        return None


# Function to extract text from the data and form a paragraph
def extract_text_to_paragraph(data):
    paragraph = " ".join(item["text"] for sublist in data for item in sublist)
    return paragraph


def prime_the_data(file_path="output.txt"):
    # Read data from 'output.txt' and store it in 'data'
    data = read_and_convert_data(file_path)

    # Check if data is successfully read
    if data is not None:
        paragraph = extract_text_to_paragraph(data)
        return paragraph
    else:
        print("Failed to load data.")


def main():
    parser = argparse.ArgumentParser(description="Process a YouTube video")
    parser.add_argument(
        "file_path",
        nargs="?",
        default="CO-6iqCum1w.pk",
        type=str,
        help="The YouTube video transcript to process",
    )
    args = parser.parse_args()
    file_path = args.file_path

    ## first, run youtube_transcript_api CO-6iqCum1w > CO-6iqCum1w.pk

    ## then we clean it up
    transcript = prime_the_data(file_path)

    ## then we process this transcript
    output = describe_transcript_with_llm(transcript)
    print(output)


if __name__ == "__main__":
    main()
