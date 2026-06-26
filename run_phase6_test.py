import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

def test_endpoint(url: str, description: str) -> None:
    print(f"\nTesting: {description} ({url})")
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status = response.status
            body = response.read().decode("utf-8")
            data = json.loads(body)
            print(f"Status: {status} OK")
            print("Response Snippet:")
            # Print a clean snippet of the returned JSON
            print(json.dumps(data, indent=2)[:300] + "\n..." if len(json.dumps(data)) > 300 else json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
        raise
    except Exception as e:
        print(f"Request Error: {e}")
        raise

def main() -> None:
    print("="*60)
    print("Starting REST API Verification Server...")
    print("="*60)
    
    # Locate project root and executable
    project_root = Path(__file__).resolve().parent
    python_exe = project_root / "venv" / "Scripts" / "python.exe"
    
    if not python_exe.exists():
        python_exe = sys.executable  # Fallback to current python
        
    # Command to run uvicorn
    # python -m uvicorn src.dashboard.api:app --host 127.0.0.1 --port 8000
    cmd = [str(python_exe), "-m", "uvicorn", "src.dashboard.api:app", "--host", "127.0.0.1", "--port", "8000"]
    
    # Start the server as a subprocess
    server_process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give uvicorn a few seconds to start up
    time.sleep(4)
    
    # Check if server started successfully
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print("Failed to start Uvicorn server:")
        print(stderr)
        sys.exit(1)
        
    try:
        # Verify endpoints
        test_endpoint("http://127.0.0.1:8000/health", "Health Status")
        test_endpoint("http://127.0.0.1:8000/profile", "Latest Profile Snapshot")
        test_endpoint("http://127.0.0.1:8000/posts/top?limit=2", "Top 2 Posts by Engagement")
        test_endpoint("http://127.0.0.1:8000/analytics/summary", "Analytics Summary Statistics")
        
        print("\n" + "="*60)
        print("REST API Verification: SUCCESS")
        print("Endpoints Verified: /health, /profile, /posts/top, /analytics/summary")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nREST API Verification: FAILED - {e}\n")
        # Print server logs for debugging
        print("--- Uvicorn Server Logs ---")
        try:
            stdout, stderr = server_process.communicate(timeout=2)
            print("STDOUT:")
            print(stdout)
            print("STDERR:")
            print(stderr)
        except Exception as comm_err:
            print(f"Could not retrieve server logs: {comm_err}")
        sys.exit(1)
        
    finally:
        print("Stopping Uvicorn verification server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")

if __name__ == "__main__":
    main()
