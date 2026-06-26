import os
import sys
import subprocess
from pathlib import Path

def main() -> None:
    print("=" * 60)
    print("Starting LinkedIn AI Streamlit Dashboard...")
    print("=" * 60)
    
    project_root = Path(__file__).resolve().parent
    python_exe = project_root / "venv" / "Scripts" / "python.exe"
    
    if not python_exe.exists():
        python_exe = sys.executable  # Fallback to current python
        
    cmd = [str(python_exe), "-m", "streamlit", "run", "src/dashboard/app.py"]
    
    try:
        subprocess.run(cmd, cwd=str(project_root), check=True)
    except KeyboardInterrupt:
        print("\nDashboard server stopped by user.")
    except Exception as e:
        print(f"Error launching Streamlit server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
