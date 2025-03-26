import multiprocessing
from google import genai
from io import BytesIO
import os 

# Configure the API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Please provide an API key.")


# Global model object (needs to be re-initialized inside subprocess)
client = None


def init_model():
    global client
    client = genai.Client(api_key=api_key)


def run_generation(prompt):
    global client
    try:
        mock_attachment = BytesIO(b"")
        mock_attachment.read()  # Seek to end of file
        client.files.upload(
            file=mock_attachment, config=dict(mime_type="application/pdf")
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[mock_attachment, prompt]
        )
        return response.text
    except ValueError as e:
        return f"Error: {e}"


if __name__ == "__main__":
    prompts = [
        "Explain the theory of relativity.",
        "What is the capital of France?",
        "Write a Python function to sort a list.",
    ]

    with multiprocessing.Pool(initializer=init_model) as pool:
        results = pool.map(run_generation, prompts)

    for r in results:
        print(r)
