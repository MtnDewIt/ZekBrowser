import asyncio
import json
import logging
import socket
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Dict, List, Set, Any, Optional

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# --- Configuration ---
DEWRITO_JSON_PATH = "dewrito.json"
REFRESH_INTERVAL = 15  # seconds
API_TIMEOUT = 5.0      # seconds (timeout for querying individual servers)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global State (Cache) ---
# We use a global dictionary to store the cached API response.
# Since asyncio runs on a single thread, swapping the reference to this dict is atomic.
api_cache: Dict[str, Any] = {}

app = FastAPI()

# --- Helper Functions ---

def get_current_http_date() -> str:
    """Returns the current date in HTTP format (RFC 1123)."""
    return formatdate(timeval=None, localtime=False, usegmt=True)

async def resolve_reverse_dns(ip: str) -> Optional[str]:
    """Resolves IP to hostname asynchronously without blocking the loop."""
    loop = asyncio.get_running_loop()
    try:
        # run_in_executor allows blocking socket calls to run in a thread
        host_info = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
        return host_info[0]
    except Exception:
        return None

async def fetch_master_list(client: httpx.AsyncClient, url: str) -> List[str]:
    """Queries a single master server and returns a list of IP:Port strings."""
    try:
        response = await client.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Check structure: {"result": {"servers": [...]}}
        if "result" in data and "servers" in data["result"]:
            return data["result"]["servers"]
    except Exception as e:
        logger.warning(f"Failed to query master server {url}: {e}")
    return []

async def fetch_game_server_info(client: httpx.AsyncClient, ip_port: str) -> Optional[Dict[str, Any]]:
    """Queries a specific game server and formats the data."""
    try:
        # Assume HTTP protocol for the query based on the prompt
        url = f"http://{ip_port}/"
        response = await client.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        server_data = response.json()
        
        # We need to extract the IP from the string "127.0.0.1:8080"
        ip_address = ip_port.split(':')[0]
        
        # Attempt Reverse DNS (optional, but present in requested output)
        # We run this concurrently with the data processing to save time? 
        # Actually, let's just do it here.
        rdns = await resolve_reverse_dns(ip_address)
        
        if rdns:
            server_data['reverseDns'] = rdns
            
        # Add 'firstSeenAt' - In a real DB app this is persistent, 
        # but for a memory-cache script, we'll set it to now or keep it if we had persistence.
        # For this logic, we just set it to current refresh time to match schema validity.
        server_data['firstSeenAt'] = get_current_http_date()

        # Generate short version if not present
        if 'eldewritoVersion' in server_data:
             server_data['eldewritoVersionShort'] = server_data['eldewritoVersion'].split('-')[0]

        return ip_port, server_data
    except Exception as e:
        # Server might be offline or unreachable
        return None

async def update_server_cache():
    """Main logic: Pulls master lists, dedupes, queries servers, updates cache."""
    global api_cache
    
    # 1. Load Master Server URLs from local JSON
    try:
        with open(DEWRITO_JSON_PATH, 'r') as f:
            config = json.load(f)
            master_entries = config.get("masterServers", [])
            # Extract only the 'list' attribute
            master_urls = [m['list'] for m in master_entries if 'list' in m]
    except Exception as e:
        logger.error(f"Error reading {DEWRITO_JSON_PATH}: {e}")
        return

    async with httpx.AsyncClient() as client:
        # 2. Query all master servers concurrently
        logger.info(f"Querying {len(master_urls)} master servers...")
        master_tasks = [fetch_master_list(client, url) for url in master_urls]
        results = await asyncio.gather(*master_tasks)

        # 3. Deduplicate IP:Port combos
        unique_servers: Set[str] = set()
        for server_list in results:
            for ip_port in server_list:
                unique_servers.add(ip_port)
        
        logger.info(f"Found {len(unique_servers)} unique game servers. Querying details...")

        # 4. Query all game servers concurrently
        # We limit concurrency slightly to avoid file descriptor limits if the list is huge,
        # but for <100 servers, full concurrency is fine.
        game_tasks = [fetch_game_server_info(client, srv) for srv in unique_servers]
        game_results = await asyncio.gather(*game_tasks)

        # 5. Build the final data structure
        successful_servers = {}
        total_players = 0
        
        for res in game_results:
            if res:
                ip_port, data = res
                successful_servers[ip_port] = data
                
                # Safely add player count
                if "numPlayers" in data:
                    try:
                        total_players += int(data["numPlayers"])
                    except ValueError:
                        pass

        # 6. Format Final JSON
        new_cache = {
            "count": {
                "players": total_players,
                "servers": len(successful_servers)
            },
            "updatedAt": get_current_http_date(),
            "servers": successful_servers
        }

        # Atomically update global cache
        api_cache = new_cache
        logger.info(f"Cache updated. Servers: {len(successful_servers)}, Players: {total_players}")

# --- Background Task Loop ---

async def background_refresher():
    """Runs the update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_server_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

# --- FastAPI Events & Routes ---

@app.on_event("startup")
async def startup_event():
    # Start the background task when the API starts
    asyncio.create_task(background_refresher())

@app.get("/api/")
async def get_stats():
    # Serve the cached data. If cache is empty (startup), return 503 or empty structure.
    if not api_cache:
        return JSONResponse(
            status_code=503, 
            content={"error": "Server is warming up, please try again in a few seconds."}
        )
    return api_cache

# --- Entry Point ---

if __name__ == "__main__":
    # In production, you would run this via command line: uvicorn server:app --host 0.0.0.0 --port 80
    uvicorn.run(app, host="0.0.0.0", port=8000)