import subprocess
import time
import os
import signal

def run_command(command):
    try:
        result = subprocess.run(
            ["./venv/bin/python", "cli.py"] + command,
            capture_output=True,
            text=True
        )
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def test_cases():
    print("-" * 30)
    print("CLI TESTING - START")
    print("-" * 30)

    # 1. Upload text file
    res = run_command(["upload-text", "sample.txt"])
    if res.returncode == 0 and "Successfully uploaded: sample.txt" in res.stdout:
        print("PASS - upload text file")
    else:
        print(f"FAIL - upload text file: {res.stderr or res.stdout}")

    # 2. List uploaded texts
    res = run_command(["list-texts"])
    if res.returncode == 0 and "sample.txt" in res.stdout:
        print("PASS - list uploaded texts")
    else:
        print(f"FAIL - list uploaded texts: {res.stderr or res.stdout}")

    # 3. Generate audio
    # NOTE: This might fail if SARVAM_API_KEY is not set or invalid
    res = run_command(["generate-audio", "sample.txt"])
    audio_filename = None
    if res.returncode == 0 and "Successfully generated:" in res.stdout:
        print("PASS - generate audio")
        audio_filename = res.stdout.split("Successfully generated: ")[1].strip()
    else:
        # Check if it failed due to missing API key
        if "Sarvam API Error" in (res.stderr or res.stdout) or "Sarvam API Key not configured" in (res.stderr or res.stdout):
             print(f"FAIL - generate audio (Check SARVAM_API_KEY): {res.stdout.strip()}")
        else:
             print(f"FAIL - generate audio: {res.stderr or res.stdout}")

    # 4. List audio files
    if audio_filename:
        res = run_command(["list-audio"])
        if res.returncode == 0 and audio_filename in res.stdout:
            print("PASS - list audio")
        else:
            print(f"FAIL - list audio: {res.stderr or res.stdout}")

    # 5. Download audio
    if audio_filename:
        res = run_command(["download-audio", audio_filename, "--output-path", "test_output.mp3"])
        if res.returncode == 0 and os.path.exists("test_output.mp3"):
            print("PASS - download audio")
            os.remove("test_output.mp3")
        else:
            print(f"FAIL - download audio: {res.stderr or res.stdout}")

    # 6. Error Case: Upload invalid file
    with open("invalid.bin", "wb") as f:
        f.write(b"\x00\x01\x02")
    res = run_command(["upload-text", "invalid.bin"])
    if res.returncode != 0 and "Only .txt files are allowed" in (res.stderr or res.stdout):
        print("PASS - invalid file upload (caught expected error)")
    else:
        print(f"FAIL - invalid file upload: {res.stderr or res.stdout}")
    os.remove("invalid.bin")

    # 7. Error Case: Generate audio for missing text
    res = run_command(["generate-audio", "missing_file.txt"])
    if res.returncode != 0 and "Text file not found" in (res.stderr or res.stdout):
        print("PASS - generate audio for missing text (caught expected error)")
    else:
        print(f"FAIL - generate audio for missing text: {res.stderr or res.stdout}")

    print("-" * 30)
    print("CLI TESTING - COMPLETE")
    print("-" * 30)

if __name__ == "__main__":
    # Start server
    server_process = subprocess.Popen(
        ["./venv/bin/python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3) # Wait for server to start

    try:
        test_cases()
    finally:
        # Stop server
        server_process.terminate()
        server_process.wait()
