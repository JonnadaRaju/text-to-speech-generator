import typer
import requests
import os
from typing import Optional

app = typer.Typer(help="Telugu TTS Generator CLI")
API_URL = "http://127.0.0.1:8000"

@app.command()
def upload_text(file_path: str):
    """Upload a text file."""
    if not os.path.exists(file_path):
        typer.echo(f"Error: File not found at {file_path}")
        raise typer.Exit(code=1)
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(f"{API_URL}/texts/upload", files=files)
    
    if response.status_code == 200:
        typer.echo(f"Successfully uploaded: {response.json()['filename']}")
    else:
        typer.echo(f"Error ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)

@app.command()
def list_texts():
    """List uploaded text files."""
    response = requests.get(f"{API_URL}/texts")
    if response.status_code == 200:
        texts = response.json()
        if not texts:
            typer.echo("No text files uploaded.")
        for text in texts:
            typer.echo(f"- {text}")
    else:
        typer.echo(f"Error ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)

@app.command()
def generate_audio(text_filename: str, speaker: str = "anushka"):
    """Generate audio for a text file."""
    payload = {"text_filename": text_filename, "speaker": speaker}
    response = requests.post(f"{API_URL}/audio/generate", json=payload)
    
    if response.status_code == 200:
        typer.echo(f"Successfully generated: {response.json()['filename']}")
    else:
        typer.echo(f"Error ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)

@app.command()
def list_audio():
    """List generated audio files."""
    response = requests.get(f"{API_URL}/audio")
    if response.status_code == 200:
        audios = response.json()
        if not audios:
            typer.echo("No audio files generated.")
        for audio in audios:
            typer.echo(f"- {audio}")
    else:
        typer.echo(f"Error ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)

@app.command()
def download_audio(filename: str, output_path: Optional[str] = None):
    """Download generated audio."""
    response = requests.get(f"{API_URL}/audio/{filename}")
    if response.status_code == 200:
        if not output_path:
            output_path = filename
        with open(output_path, "wb") as f:
            f.write(response.content)
        typer.echo(f"Successfully downloaded to: {output_path}")
    else:
        typer.echo(f"Error ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
