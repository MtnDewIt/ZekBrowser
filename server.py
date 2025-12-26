import asyncio
import json
import logging
import socket
import sqlite3
from datetime import datetime, timezone
from email.utils import formatdate
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# --- Configuration ---
DEWRITO_JSON_PATH = "dewrito.json"
REFRESH_INTERVAL = 15  # seconds
STATS_INTERVAL = 300   # 5 minutes in seconds
API_TIMEOUT = 5.0      # seconds
DB_PATH = "database/database.sqlite"
LEGACY_STATS_URL = "https://eldewrito.pauwlo.com/api/stats"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global State (Cache) ---
# We use a global dictionary to store the cached API response.
# Since asyncio runs on a single thread, swapping the reference to this dict is atomic.
api_cache: Dict[str, Any] = {}

app = FastAPI()

# --- Database Functions ---

async def fetch_legacy_stats() -> Optional[Dict[str, List[List[int]]]]:
    """Fetch historical stats from legacy API."""
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching legacy stats from {LEGACY_STATS_URL}...")
            response = await client.get(LEGACY_STATS_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            # Validate structure
            if "players" in data and "servers" in data:
                if isinstance(data["players"], list) and isinstance(data["servers"], list):
                    logger.info(f"Successfully fetched {len(data['players'])} historical data points")
                    return data
            
            logger.warning("Legacy stats API returned unexpected format")
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch legacy stats: {e}")
        return None

def populate_stats_from_legacy(legacy_data: Dict[str, List[List[int]]]):
    """Populate database with legacy stats data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Combine players and servers data by timestamp
        players_dict = {entry[0]: entry[1] for entry in legacy_data.get("players", [])}
        servers_dict = {entry[0]: entry[1] for entry in legacy_data.get("servers", [])}
        
        # Get all unique timestamps
        all_timestamps = set(players_dict.keys()) | set(servers_dict.keys())
        
        records_added = 0
        for timestamp_ms in sorted(all_timestamps):
            # Convert milliseconds to datetime
            timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            
            player_count = players_dict.get(timestamp_ms, 0)
            server_count = servers_dict.get(timestamp_ms, 0)
            
            cursor.execute("""
                INSERT INTO server_stats (player_count, server_count, recorded_at)
                VALUES (?, ?, ?)
            """, (player_count, server_count, timestamp_dt))
            
            records_added += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully populated database with {records_added} historical records")
    except Exception as e:
        logger.error(f"Failed to populate stats from legacy data: {e}")

async def init_db():
    """Initialize the stats table and populate with legacy data if empty."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if server_stats table exists, if not create it
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_count INTEGER NOT NULL DEFAULT 0,
            server_count INTEGER NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recorded_at 
        ON server_stats(recorded_at)
    """)
    
    # Check if table is empty
    cursor.execute("SELECT COUNT(*) FROM server_stats")
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized")
    
    # If table is empty, try to populate with legacy data
    if count == 0:
        logger.info("Stats table is empty, attempting to fetch legacy data...")
        legacy_data = await fetch_legacy_stats()
        
        if legacy_data and (legacy_data.get("players") or legacy_data.get("servers")):
            populate_stats_from_legacy(legacy_data)
        else:
            logger.info("No legacy data available, starting with empty stats database")

def save_stats(player_count: int, server_count: int):
    """Save current stats to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        
        cursor.execute("""
            INSERT INTO server_stats (player_count, server_count, recorded_at)
            VALUES (?, ?, ?)
        """, (player_count, server_count, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved stats: {server_count} servers, {player_count} players")
    except Exception as e:
        logger.error(f"Failed to save stats: {e}")

def get_stats_history() -> Dict[str, List[List[int]]]:
    """Retrieve historical stats from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%s', recorded_at) AS INTEGER) * 1000 as timestamp,
                player_count,
                server_count
            FROM server_stats
            ORDER BY recorded_at ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        players = [[row[0], row[1]] for row in rows]
        servers = [[row[0], row[2]] for row in rows]
        
        return {
            "players": players,
            "servers": servers
        }
    except Exception as e:
        logger.error(f"Failed to retrieve stats: {e}")
        return {
            "players": [],
            "servers": []
        }

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

async def fetch_server_mods(client: httpx.AsyncClient, ip_port: str) -> Optional[Dict[str, Any]]:
    """Queries a specific game server's /mods endpoint and returns mod data."""
    try:
        url = f"http://{ip_port}/mods"
        response = await client.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        mods_data = response.json()
        return mods_data
    except Exception as e:
        # Server might not have mods endpoint or it's unreachable
        logger.debug(f"Failed to fetch mods from {ip_port}: {e}")
        return None

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
        version_short = None
        if 'eldewritoVersion' in server_data:
             version_short = server_data['eldewritoVersion'].split('-')[0]
             server_data['eldewritoVersionShort'] = version_short

        # Fetch mods data (Will need to update this if we ever get to 0.8)
        if version_short and version_short.startswith("0.7"):
            mods_data = await fetch_server_mods(client, ip_port)
            if mods_data:
                server_data['mods'] = mods_data

        return ip_port, server_data
    except Exception as e:
        # Server might be offline or unreachable
        logger.debug(f"Failed to fetch server info from {ip_port}: {e}")
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

# --- Background Task Loops ---

async def background_refresher():
    """Runs the update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_server_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

async def background_stats_recorder():
    """Records stats to database every 5 minutes."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        
        if api_cache and "count" in api_cache:
            player_count = api_cache["count"].get("players", 0)
            server_count = api_cache["count"].get("servers", 0)
            save_stats(player_count, server_count)

# --- FastAPI Events & Routes ---

@app.on_event("startup")
async def startup_event():
    # Initialize database (will populate with legacy data if empty)
    await init_db()
    
    # Start background tasks
    asyncio.create_task(background_refresher())
    asyncio.create_task(background_stats_recorder())

@app.get("/api/")
async def get_current_stats():
    """Serve the current cached server data."""
    if not api_cache:
        return JSONResponse(
            status_code=503, 
            content={"error": "Server is warming up, please try again in a few seconds."}
        )
    return api_cache

@app.get("/api/stats")
async def get_historical_stats():
    """Serve historical stats data for charting."""
    stats = get_stats_history()
    return stats

# --- Entry Point ---

if __name__ == "__main__":
    # In production, you would run this via command line: uvicorn server:app --host 0.0.0.0 --port 80
    uvicorn.run(app, host="0.0.0.0", port=8001)