import asyncio
import sys
from dotenv import load_dotenv
from src.auth.login import LinkedInAuthenticator
from src.utils.logger import setup_logger

# Load environment variables from .env
load_dotenv()

# Setup logger for check_session
logger = setup_logger("check_session")

async def main() -> None:
    """Verifies the saved session status and outputs verification results."""
    logger.info("Starting session check script...")
    
    try:
        authenticator = LinkedInAuthenticator()
        
        # Verify existing session (this opens Chromium headlessly and navigates to the feed)
        session_valid = await authenticator.verify_session()
        
        if session_valid:
            logger.info("Result: Session is valid and usable.")
            print("Session Valid")
            sys.exit(0)
        else:
            logger.warning("Result: Session is invalid or has expired.")
            print("Session Expired")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Exception encountered during session verification: {e}", exc_info=True)
        print("Session Expired")
        sys.exit(1)

if __name__ == "__main__":
    # Apply standard Windows asyncio policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(main())
