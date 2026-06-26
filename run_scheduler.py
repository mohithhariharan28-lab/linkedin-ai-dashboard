import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.utils.scheduler import PipelineScheduler

async def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn AI Analytics Pipeline Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Start background scheduler loop")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds (default: 3600)")
    parser.add_argument("--run-now", action="store_true", help="Trigger a pipeline run immediately")
    
    args = parser.parse_args()
    
    scheduler = PipelineScheduler(interval_seconds=args.interval)
    
    if args.run_now:
        print("Executing pipeline immediately...")
        await scheduler.run_pipeline_task()
        
    if args.daemon:
        print(f"Starting background pipeline scheduler (polling every {args.interval}s)...")
        try:
            await scheduler.start_loop()
        except KeyboardInterrupt:
            scheduler.stop()
            print("Scheduler stopped.")
    elif not args.run_now:
        parser.print_help()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
        sys.exit(0)
