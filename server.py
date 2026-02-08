import anyio
import asyncio
import json
import logging
import socket
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Union

import httpx
import uvicorn
import re
from fastapi import FastAPI
from fastapi.responses import JSONResponse

REFRESH_INTERVAL = 15  # seconds
STATS_INTERVAL = 300   # seconds
API_TIMEOUT = 5.0      # seconds
DB_PATH = "database/database.sqlite"

# --- ElDewrito configuration ---
ELDEWRITO_MASTER_LIST = "dewrito.json"
LEGACY_ELDEWRITO_STATS_URL = "https://eldewrito.pauwlo.com/api/stats"

# --- Cartographer configuration ---
CARTOGRAPHER_BASE = "https://cartographer.online"
CARTOGRAPHER_LIST_URL = f"{CARTOGRAPHER_BASE}/live/server_list.php"
CARTOGRAPHER_SERVER_URL = f"{CARTOGRAPHER_BASE}/live/servers"
CARTOGRAPHER_WORKERS = 16

# --- Cartographer Property Maps ---
PROPERTY_MAP = {
    1073775152: "server_name",
    536904239:  "xuid",
    536904219:  "unknown_int64_1",
    1073775141: "server_desc",
    268468743:  "map_id",
    1073775142: "map_name",
    1073775143: "map_hash_1",
    1073775144: "gametype_name",
    268468744:  "unknown_int32_1",
    268468745:  "gametype_id",
    268468746:  "map_id_2",
    1073775145: "map_name_2",
    1073775146: "map_hash_2",
    1073775147: "gametype_name_2",
    268468747:  "unknown_int32_2",
    268468748:  "unknown_int32_3",
    268468749:  "unknown_int32_4",
    268468750:  "version_1",
    268468751:  "version_2",
    268468752:  "party_privacy",
    268468753:  "game_status",
    268468754:  "unknown_int32_6",
    268468755:  "unknown_int32_7",
}

# --- Cartographer Map Info Table ---
MAP_ID_TO_INFO = {
    1:      ("00a_introduction",   "The Heretic"),
    101:    ("01a_tutorial",       "Armory"),
    105:    ("01b_spacestation",   "Cairo Station"),
    301:    ("03a_oldmombasa",     "Outskirts"),
    305:    ("03b_newmombasa",     "Metropolis"),
    401:    ("04a_gasgiant",       "The Arbiter"),
    405:    ("04b_floodlab",       "Oracle"),
    501:    ("05a_deltaapproach",  "Delta Halo"),
    505:    ("05b_deltatowers",    "Regret"),
    601:    ("06a_sentinelwalls",  "Sacred Icon"),
    605:    ("06b_floodzone",      "Quarantine Zone"),
    701:    ("07a_highcharity",    "Gravemind"),
    801:    ("07b_forerunnership", "High Charity"),
    705:    ("08a_deltacliffs",    "Uprising"),
    805:    ("08b_deltacontrol",   "The Great Journey"),
    80:     ("ascension",          "Ascension"),
    1201:   ("backwash",           "Backwash"),
    100:    ("beavercreek",        "Beaver Creek"),
    60:     ("burial_mounds",      "Burial Mounds"),
    110:    ("coagulation",        "Coagulation"),
    70:     ("colossus",           "Colossus"),
    1300:   ("containment",        "Containment"),
    10:     ("cyclotron",          "Ivory Tower"),
    1302:   ("deltatap",           "Sanctuary"),
    1400:   ("derelict",           "Desolation"),
    3001:   ("derelict",           "Desolation"),
    1200:   ("dune",               "Relic"),
    1001:   ("elongation",         "Elongation"),
    120:    ("foundation",         "Foundation"),
    1002:   ("gemini",             "Gemini"),
    800:    ("headlong",           "Headlong"),
    1402:   ("highplains",         "Tombstone"),
    3000:   ("highplains",         "Tombstone"),
    50:     ("lockout",            "Lockout"),
    20:     ("midship",            "Midship"),
    444678: ("needle",             "Uplift"),
    91101:  ("street_sweeper",     "District"),
    1101:   ("triplicate",         "Terminal"),
    1000:   ("turf",               "Turf"),
    1109:   ("warlock",            "Warlock"),
    40:     ("waterworks",         "Waterworks"),
    30:     ("zanzibar",           "Zanzibar"),
}

# --- Cartographer Gametype Table ---
GAMETYPE_ID_TO_NAME = {
    0: "None",
    1: "CTF",
    2: "Slayer",
    3: "Oddball",
    4: "KOTH",
    5: "Race",
    6: "Headhunter",
    7: "Juggernaut",
    8: "Territories",
    9: "Assault",
    10: "Stub",
}

# --- GameSpy Protocol Implementation ---
class GameKeys(Enum):
    HALO = "QW88cv"
    HALOD = "yG3d9w"
    HALOMACD = "e4Rd9J"
    HALOMAC = "e4Rd9J"
    HALOM = "e4Rd9J"
    HALOR = "e4Rd9J"

GAMESPY_IP_PORT_LENGTH = 6

class GameSpyFlags:
    A, B, C, D = 0x02, 0x08, 0x10, 0x20

@dataclass
class GameSpyServerAddress:
    address: str
    port: int

@dataclass
class GameSpyServer:
    address: str
    port: int
    game: Optional[str] = None

@dataclass
class GameSpyServerResponse:
    address: str
    port: int
    game: Optional[str]
    data: Union[str, Dict[str, Any]]

# GameSpy Decryption Algorithm
def _enctypex_func5(encxkey: bytearray, cnt: int, id_bytes: bytes, idlen: int, n1: int, n2: int) -> tuple:
    if cnt == 0: return 0, n1, n2
    mask = 1
    if cnt > 1:
        while mask < cnt: mask = (mask << 1) + 1
    i = 0
    while True:
        n1 = encxkey[n1 & 0xff] + id_bytes[n2]
        n2 += 1
        if n2 >= idlen:
            n2 = 0
            n1 += idlen
        tmp = n1 & mask
        i += 1
        if i > 11: tmp %= cnt
        if tmp <= cnt: break
    return tmp, n1, n2

def _enctypex_func4(encxkey: bytearray, id_bytes: bytes, idlen: int):
    if idlen < 1: return
    for i in range(256): encxkey[i] = i
    n1 = n2 = 0
    for i in range(255, -1, -1):
        t1, n1, n2 = _enctypex_func5(encxkey, i, id_bytes, idlen, n1, n2)
        t2 = encxkey[i]
        encxkey[i] = encxkey[t1]
        encxkey[t1] = t2
    encxkey[256] = encxkey[1]
    encxkey[257] = encxkey[3]
    encxkey[258] = encxkey[5]
    encxkey[259] = encxkey[7]
    encxkey[260] = encxkey[n1 & 0xff]

def _enctypex_func7(encxkey: bytearray, d: int) -> int:
    a = encxkey[256]
    b = encxkey[257]
    c = encxkey[a]
    encxkey[256] = (a + 1) & 0xff
    encxkey[257] = (b + c) & 0xff
    a = encxkey[260]
    b = encxkey[257]
    b = encxkey[b]
    c = encxkey[a]
    encxkey[a] = b
    a = encxkey[259]
    b = encxkey[257]
    a = encxkey[a]
    encxkey[b] = a
    a = encxkey[256]
    b = encxkey[259]
    a = encxkey[a]
    encxkey[b] = a
    a = encxkey[256]
    encxkey[a] = c
    b = encxkey[258]
    a = encxkey[c]
    c = encxkey[259]
    b = (b + a) & 0xff
    encxkey[258] = b
    a = b
    c = encxkey[c]
    b = encxkey[257]
    b = encxkey[b]
    a = encxkey[a]
    c = (c + b) & 0xff
    b = encxkey[260]
    b = encxkey[b]
    c = (c + b) & 0xff
    b = encxkey[c]
    c = encxkey[256]
    c = encxkey[c]
    a = (a + c) & 0xff
    c = encxkey[b]
    b = encxkey[a]
    encxkey[260] = d & 0xff
    c = c ^ b ^ (d & 0xff)
    encxkey[259] = c & 0xff
    return c & 0xff

def _enctypex_func6(encxkey: bytearray, data: bytearray, length: int) -> int:
    for i in range(length): data[i] = _enctypex_func7(encxkey, data[i])
    return length

def _enctypex_funcx(encxkey: bytearray, key: bytes, encxvalidate: bytearray, data: bytes, datalen: int):
    keylen = len(key)
    for i in range(datalen):
        idx1 = (key[i % keylen] * i) & 7
        idx2 = i & 7
        encxvalidate[idx1] = (encxvalidate[idx1] ^ encxvalidate[idx2] ^ data[i]) & 0xff
    _enctypex_func4(encxkey, bytes(encxvalidate), 8)

def _enctypex_init(encxkey: bytearray, key: bytes, validate: bytes, data: bytearray) -> tuple:
    datalen = len(data)
    if datalen < 1: return None, 0
    a = (data[0] ^ 0xec) + 2
    if datalen < a: return None, 0
    b = data[a - 1] ^ 0xea
    if datalen < (a + b): return None, 0
    encxvalidate = bytearray(validate[:8])
    _enctypex_funcx(encxkey, key, encxvalidate, bytes(data[a:a+b]), b)
    a += b
    return data[a:], a

def _enctypex_decoder(key: bytes, validate: bytes, data: bytes) -> bytes:
    encxkey = bytearray(261)
    data_array = bytearray(data)
    result, offset = _enctypex_init(encxkey, key, validate, data_array)
    if result is None: return None
    result_array = bytearray(result)
    _enctypex_func6(encxkey, result_array, len(result_array))
    return bytes(result_array)

def _gamespy_decryptx(key: str, validate: str, data: bytes) -> bytes:
    try:
        return _enctypex_decoder(key.encode('ascii'), validate.encode('ascii'), data)
    except: return None

def _make_validation_key() -> str:
    return format(int(time.time() * 1000), 'x')[-8:].zfill(8)

class GameSpyUDPClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
    def close(self):
        try: self.socket.close()
        except: pass
    def send_query(self, address: str, port: int, data: str):
        try:
            self.socket.sendto(data.encode('utf-8'), (address, port))
            return True
        except: return False
    async def write(self, address: str, port: int, data: str):
        return await asyncio.get_event_loop().run_in_executor(None, self.send_query, address, port, data)
    def receive_responses(self, end_delay: float = 0.5) -> Optional[List[Dict]]:
        responses = []
        last_receive_time = time.time()
        while True:
            try:
                data, addr = self.socket.recvfrom(4096)
                responses.append({'address': addr[0], 'port': addr[1], 'data': data})
                last_receive_time = time.time()
            except socket.timeout:
                if time.time() - last_receive_time > end_delay: break
            except: break
        return responses if responses else None
    async def read_all(self, end_delay: float = 0.5) -> Optional[List[Dict]]:
        return await asyncio.get_event_loop().run_in_executor(None, self.receive_responses, end_delay)

class GameSpyTCPClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host, self.port, self.timeout = host, port, timeout
        self.socket = None
    async def connect(self):
        def _conn():
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        await asyncio.get_event_loop().run_in_executor(None, _conn)
    async def request(self, data: bytes) -> bytes:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.socket.sendall, data)
        response = b''
        while True:
            try:
                chunk = await asyncio.wait_for(loop.run_in_executor(None, self.socket.recv, 4096), timeout=1.0)
                if not chunk: break
                response += chunk
            except asyncio.TimeoutError: break
        return response
    def close(self):
        if self.socket: self.socket.close()

def _encode_master_server_request(game: str, validation_key: str) -> bytes:
    def cstring(s: str) -> List[int]: return [ord(c) for c in s] + [0]
    data = [0, 0, 0] + [1, 3, 0, 0, 0, 0] + cstring(game) + cstring(game) + cstring(validation_key) + [0]*5
    data[1] = len(data)
    return bytes(data)

def _decode_master_server_response(data: bytes) -> Optional[Dict]:
    if len(data) < GAMESPY_IP_PORT_LENGTH: return None
    scanner = 0
    request_ip = '.'.join(str(b) for b in data[scanner:scanner+4])
    common_port = (data[scanner+4] << 8) | data[scanner+5]
    scanner += GAMESPY_IP_PORT_LENGTH
    if common_port == 0xFFFF: return None
    def extract_pascal_string(offset: int):
        if offset >= len(data): return "", offset
        size = data[offset]
        return data[offset+1:offset+1+size].decode('ascii', errors='ignore'), offset + size + 1
    _, scanner = extract_pascal_string(scanner)
    _, scanner = extract_pascal_string(scanner)
    servers = []
    while scanner < len(data):
        flag = data[scanner]
        scanner += 1
        extra_len = sum([3 if flag & GameSpyFlags.A else 0, 4 if flag & GameSpyFlags.B else 0, 2 if flag & GameSpyFlags.C else 0, 2 if flag & GameSpyFlags.D else 0])
        if scanner + GAMESPY_IP_PORT_LENGTH > len(data): break
        ip = '.'.join(str(b) for b in data[scanner:scanner+4])
        port = (data[scanner+4] << 8) | data[scanner+5]
        scanner += GAMESPY_IP_PORT_LENGTH + extra_len - 1
        if flag == 0 and ip == "255.255.255.255": break
        servers.append(GameSpyServerAddress(address=ip, port=port))
    return {'request_ip': request_ip, 'servers': servers}

async def _get_gamespy_master_server_list(game, host="hosthpc.com", port=28910, timeout=5.0):
    game_map = {'halom':'HALOM','halor':'HALOR','halod':'HALOD','halomac':'HALOMAC','halomacd':'HALOMACD','halo':'HALO'}
    game_enum = game_map.get(game.lower())
    if not game_enum: return []
    client = GameSpyTCPClient(host, port, timeout)
    try:
        await client.connect()
        vkey = _make_validation_key()
        encrypted = await client.request(_encode_master_server_request(game, vkey))
        decrypted = _gamespy_decryptx(GameKeys[game_enum].value, vkey, encrypted)
        decoded = _decode_master_server_response(decrypted) if decrypted else None
        return decoded['servers'] if decoded else []
    except: return []
    finally: client.close()

async def _resolve_gamespy_servers(args, master_host="hosthpc.com", master_port=28910, timeout=5.0):
    servers = []
    game_map = {'ce':'halom','pc':'halor','trial':'halod','mac':'halomac','macdemo':'halomacd','beta':'halo'}
    for arg in args:
        if isinstance(arg, str):
            game_key = game_map.get(arg.lower(), arg)
            s_list = await _get_gamespy_master_server_list(game_key, master_host, master_port, timeout)
            servers.extend([GameSpyServer(s.address, s.port, arg) for s in s_list])
        else: servers.append(GameSpyServer(arg.address, arg.port))
    return servers

async def _query_gamespy_server_info(servers, timeout=2.0):
    if not servers: return None
    address_game_map = {f"{s.address}:{s.port}": s.game for s in servers}
    client = GameSpyUDPClient()
    try:
        for s in servers: await client.write(s.address, s.port, '\\')
        await asyncio.sleep(0.2)
        responses = await client.read_all(end_delay=timeout)
        if not responses: return None
        return [GameSpyServerResponse(r['address'], r['port'], address_game_map.get(f"{r['address']}:{r['port']}"), r['data'].decode('utf-8', errors='ignore')) for r in responses]
    finally: client.close()

def _clean_gamespy_string(s: str) -> str:
    result, i = [], 0
    while i < len(s):
        c = s[i]
        if ord(c) < 32 and c not in '\t\n\r': i += 1; continue
        if c == '^' and i + 1 < len(s) and (s[i+1].isdigit() or s[i+1].islower()): i += 2; continue
        if c == '\\': result.append('/'); i += 1; continue
        if 32 <= ord(c) < 127 or ord(c) >= 128: result.append(c)
        i += 1
    return ''.join(result)

def _parse_gamespy_server_info(response_str: str) -> Dict[str, Any]:
    parts = response_str.split('\\')
    if parts and parts[0] == '': parts = parts[1:]
    info = {}
    for i in range(0, len(parts) - 1, 2):
        key, value = parts[i], _clean_gamespy_string(parts[i+1])
        if value.isdigit(): value = int(value)
        elif re.match(r'^\d+\.\d+$', value): value = float(value)
        info[key] = value
    return info

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global State (Cache) ---
eldewrito_cache: Dict[str, Any] = {}
cartographer_cache: Dict[str, Any] = {}
cartographer_summarized_cache: Dict[str, Any] = {}
haloce_cache: Dict[str, Any] = {}
halopc_cache: Dict[str, Any] = {}

app = FastAPI()

# --- Cartographer Helper Functions ---

def clean_string_field(s: Any) -> Any:
    """Clean and normalize string fields from Cartographer API."""
    if not isinstance(s, str):
        return s
    s = s.strip()
    # Remove wrapping quotes
    if s.startswith('"'):
        s = s[1:]
    if s.endswith('"'):
        s = s[:-1]
    # Strip control chars but keep all other unicode
    s = ''.join(c for c in s if ord(c) >= 0x20 and ord(c) != 0x7f)
    return s.strip()

def decode_properties(pp: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Decode properties array into named fields."""
    out = {}
    raw_props = []
    pm = PROPERTY_MAP
    for prop in pp:
        pid = prop.get('dwPropertyId')
        ptype = prop.get('type')
        val = prop.get('value')
        if isinstance(val, str):
            val = clean_string_field(val)
        name = pm.get(pid)
        out_key = name if name else f"prop_{hex(pid) if isinstance(pid,int) else pid}"
        out[out_key] = { 'value': val, 'type': ptype }
        raw_props.append({ 'dwPropertyId': pid, 'type': ptype, 'value': val })
    out['_raw'] = raw_props
    return out

def summarize_server(data: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize Cartographer server data into a clean format."""
    if data is None:
        return {}
    summary = {}
    summary['xuid'] = data.get('xuid') or data.get('XUID') or None
    summary['players'] = { 'filled': data.get('dwFilledPublicSlots'), 'max': data.get('dwMaxPublicSlots') }
    pp = data.get('pProperties') or []
    decoded = decode_properties(pp)

    server_name = decoded.get('server_name', {}).get('value') or decoded.get('prop_0x40008230', {}).get('value') or ''
    server_name = server_name.strip()

    map_name = decoded.get('map_name', {}).get('value') or decoded.get('map_name_2', {}).get('value') or ''
    map_id = decoded.get('map_id', {}).get('value') or decoded.get('map_id_2', {}).get('value')

    gt1 = decoded.get('gametype_name', {}).get('value') or ''
    gt2 = decoded.get('gametype_name_2', {}).get('value') or ''

    gtid_raw = decoded.get('gametype_id', {}).get('value')
    gametype_display = ''
    if gtid_raw is not None:
        try:
            gtid_int = int(gtid_raw)
            gametype_display = GAMETYPE_ID_TO_NAME.get(gtid_int, str(gtid_int))
        except Exception:
            gametype_display = str(gtid_raw)

    variant_display = gt1 or gt2 or ''

    if not map_name and map_id is not None:
        try:
            mid = int(map_id)
            info = MAP_ID_TO_INFO.get(mid)
            if info and len(info) > 1:
                map_name = info[1]
            else:
                map_name = f"<map id {mid}>"
        except Exception:
            map_name = f"<map id {map_id}>"

    description = (decoded.get('server_desc', {}).get('value') or '').strip()

    summary['server_name'] = server_name
    summary['map_name'] = map_name
    summary['map_id'] = map_id
    summary['gametype'] = gametype_display
    summary['variant'] = variant_display
    summary['description'] = description
    summary['decoded_properties'] = decoded
    return summary

async def fetch_cartographer_server_details(client: httpx.AsyncClient, server_id: Any) -> Optional[Dict[str, Any]]:
    """Fetch details for a single Cartographer server."""
    url = f"{CARTOGRAPHER_SERVER_URL}/{server_id}"
    try:
        r = await client.get(url, timeout=15.0)
        r.raise_for_status()
        return summarize_server(r.json())
    except Exception as e:
        logger.warning(f"Failed to fetch Cartographer server {server_id}: {e}")
        return {'xuid': server_id, 'server_name': '', 'map_name': '', 'gametype': '', 'variant': '', 'description': '<failed>'}

# --- Database Functions ---

async def fetch_legacy_eldewrito_stats() -> Optional[Dict[str, List[List[int]]]]:
    """Fetch historical ElDewrito stats from legacy API."""
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching legacy ElDewrito stats from {LEGACY_ELDEWRITO_STATS_URL}...")
            response = await client.get(LEGACY_ELDEWRITO_STATS_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            if "players" in data and "servers" in data:
                if isinstance(data["players"], list) and isinstance(data["servers"], list):
                    logger.info(f"Successfully fetched {len(data['players'])} historical ElDewrito data points")
                    return data
            
            logger.warning("Legacy stats API returned unexpected format")
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch legacy ElDewrito stats: {e}")
        return None

def populate_from_legacy_eldewrito_stats(legacy_data: Dict[str, List[List[int]]]):
    """Populate ElDewrito database with legacy stats data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        players_dict = {entry[0]: entry[1] for entry in legacy_data.get("players", [])}
        servers_dict = {entry[0]: entry[1] for entry in legacy_data.get("servers", [])}
        
        all_timestamps = set(players_dict.keys()) | set(servers_dict.keys())
        
        records_added = 0
        for timestamp_ms in sorted(all_timestamps):
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
        
        logger.info(f"Successfully populated ElDewrito database with {records_added} historical records")
    except Exception as e:
        logger.error(f"Failed to populate ElDewrito stats from legacy data: {e}")

async def init_db():
    """Initialize the stats tables and populate ElDewrito stats with legacy data if empty."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ElDewrito stats table
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

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recorded_at 
        ON server_stats(recorded_at)
    """)
    
    # Cartographer stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartographer_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_count INTEGER NOT NULL DEFAULT 0,
            server_count INTEGER NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cartographer_recorded_at 
        ON cartographer_stats(recorded_at)
    """)

    # Halo CE stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS haloce_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_count INTEGER NOT NULL DEFAULT 0,
            server_count INTEGER NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_halo_ce_recorded_at 
        ON haloce_stats(recorded_at)
    """)

    # Halo PC stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS halopc_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_count INTEGER NOT NULL DEFAULT 0,
            server_count INTEGER NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_halo_pc_recorded_at 
        ON halopc_stats(recorded_at)
    """)

    # Only check ElDewrito stats for legacy data population
    cursor.execute("SELECT COUNT(*) FROM server_stats")
    eldewrito_count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized")

    # Only populate legacy data for ElDewrito stats table
    if eldewrito_count == 0:
        logger.info("ElDewrito stats table is empty, attempting to fetch legacy data...")
        legacy_data = await fetch_legacy_eldewrito_stats()
        
        if legacy_data and (legacy_data.get("players") or legacy_data.get("servers")):
            populate_from_legacy_eldewrito_stats(legacy_data)
        else:
            logger.info("No legacy data available, starting with empty ElDewrito stats database")

def save_eldewrito_stats(player_count: int, server_count: int):
    """Save current ElDewrito stats to database."""
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
        
        logger.info(f"Saved ElDewrito stats: {server_count} servers, {player_count} players")
    except Exception as e:
        logger.error(f"Failed to save ElDewrito stats: {e}")

def save_cartographer_stats(player_count: int, server_count: int):
    """Save current Cartographer stats to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        
        cursor.execute("""
            INSERT INTO cartographer_stats (player_count, server_count, recorded_at)
            VALUES (?, ?, ?)
        """, (player_count, server_count, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved Cartographer stats: {server_count} servers, {player_count} players")
    except Exception as e:
        logger.error(f"Failed to save Cartographer stats: {e}")

def save_haloce_stats(player_count: int, server_count: int):
    """Save current Halo CE stats to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        
        cursor.execute("""
            INSERT INTO haloce_stats (player_count, server_count, recorded_at)
            VALUES (?, ?, ?)
        """, (player_count, server_count, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved Halo CE stats: {server_count} servers, {player_count} players")
    except Exception as e:
        logger.error(f"Failed to save Halo CE stats: {e}")

def save_halopc_stats(player_count: int, server_count: int):
    """Save current Halo PC stats to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        
        cursor.execute("""
            INSERT INTO halopc_stats (player_count, server_count, recorded_at)
            VALUES (?, ?, ?)
        """, (player_count, server_count, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved Halo PC stats: {server_count} servers, {player_count} players")
    except Exception as e:
        logger.error(f"Failed to save Halo PC stats: {e}")

def get_eldewrito_stats_history() -> Dict[str, List[List[int]]]:
    """Retrieve historical ElDewrito stats from database."""
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
        logger.error(f"Failed to retrieve ElDewrito stats: {e}")
        return {
            "players": [],
            "servers": []
        }

def get_cartographer_stats_history() -> Dict[str, List[List[int]]]:
    """Retrieve historical Cartographer stats from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%s', recorded_at) AS INTEGER) * 1000 as timestamp,
                player_count,
                server_count
            FROM cartographer_stats
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
        logger.error(f"Failed to retrieve Cartographer stats: {e}")
        return {
            "players": [],
            "servers": []
        }

def get_haloce_stats_history() -> Dict[str, List[List[int]]]:
    """Retrieve historical Halo CE stats from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%s', recorded_at) AS INTEGER) * 1000 as timestamp,
                player_count,
                server_count
            FROM haloce_stats
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
        logger.error(f"Failed to retrieve Halo CE stats: {e}")
        return {
            "players": [],
            "servers": []
        }

def get_halopc_stats_history() -> Dict[str, List[List[int]]]:
    """Retrieve historical Halo PC stats from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%s', recorded_at) AS INTEGER) * 1000 as timestamp,
                player_count,
                server_count
            FROM halopc_stats
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
        logger.error(f"Failed to retrieve Halo PC stats: {e}")
        return {
            "players": [],
            "servers": []
        }

async def update_eldewrito_cache():
    """Main logic: Pulls master lists, dedupes, queries servers, updates cache."""
    global eldewrito_cache
    
    # 1. Load Master Server URLs from local JSON
    try:
        async with await anyio.open_file(ELDEWRITO_MASTER_LIST, 'r') as f:
            data = await f.read()
            config = json.loads(data)
            master_entries = config.get("masterServers", [])
            # Extract only the 'list' attribute
            master_urls = [m['list'] for m in master_entries if 'list' in m]
    except Exception as e:
        logger.error(f"Error reading {ELDEWRITO_MASTER_LIST}: {e}")
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
        eldewrito_cache = new_cache
        logger.info(f"ElDewrito Cache updated. Servers: {len(successful_servers)}, Players: {total_players}")

async def update_cartographer_cache():
    """Fetch Cartographer server list and update cache with summarized data."""
    global cartographer_cache, cartographer_summarized_cache
    
    try:
        async with httpx.AsyncClient(verify=False) as client:
            logger.info("Fetching Cartographer server list...")
            response = await client.get(CARTOGRAPHER_LIST_URL, timeout=15.0)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                raw_list = data.get('servers', data.get('list', data.get('data', [])))
            else:
                raw_list = []

            # Try to map servers directly first
            mapped = []
            ids = []
            for item in raw_list:
                if isinstance(item, dict) and (item.get('pProperties') or item.get('server_desc') or item.get('name')):
                    mapped.append(summarize_server(item))
                else:
                    ids.append(item)

            # If we have already summarized data, use it
            if mapped:
                logger.info(f"Using pre-summarized Cartographer data ({len(mapped)} servers)")
                summarized_servers = mapped
            else:
                # Otherwise fetch each server detail concurrently
                logger.info(f"Fetching details for {len(ids)} Cartographer servers...")
                sem = asyncio.Semaphore(CARTOGRAPHER_WORKERS)
                
                async def sem_fetch(sid):
                    async with sem:
                        return await fetch_cartographer_server_details(client, sid)

                tasks = [sem_fetch(sid) for sid in ids]
                summarized_servers = await asyncio.gather(*tasks)

            # Calculate totals
            total_players = 0
            total_servers = len(summarized_servers)
            
            for server in summarized_servers:
                if isinstance(server, dict):
                    players = server.get('players', {})
                    if isinstance(players, dict):
                        filled = players.get('filled', 0)
                        try:
                            total_players += int(filled)
                        except (ValueError, TypeError):
                            pass
            
            # Update both caches
            cartographer_cache = {
                "count": {
                    "players": total_players,
                    "servers": total_servers
                },
                "updatedAt": get_current_http_date(),
                "servers": raw_list  # Keep raw list for compatibility
            }

            cartographer_summarized_cache = {
                "count": {
                    "players": total_players,
                    "servers": total_servers
                },
                "updatedAt": get_current_http_date(),
                "servers": summarized_servers  # Processed/summarized list
            }
            
            logger.info(f"Cartographer Cache updated. Servers: {total_servers}, Players: {total_players}")
            
    except Exception as e:
        logger.error(f"Failed to update Cartographer cache: {e}")

async def update_haloce_cache():
    """Fetch Halo CE server list and update cache with summarized data."""
    global haloce_cache
    
    try:
        logger.info("Fetching Halo CE server list from master server...")
        
        servers = await _resolve_gamespy_servers(['ce'], timeout=5.0)
        
        if not servers:
            logger.warning("No Halo CE servers returned from master server")
            return
        
        logger.info(f"Found {len(servers)} Halo CE servers. Querying for details...")
        
        responses = await _query_gamespy_server_info(servers, timeout=2.0)

        server_list = []
        total_players = 0
        
        if responses:
            for resp in responses:
                info = _parse_gamespy_server_info(resp.data) if isinstance(resp.data, str) else {}
                
                player_count = info.get('numplayers', 0)
                if isinstance(player_count, int):
                    total_players += player_count
                
                server_list.append({
                    'address': resp.address,
                    'port': resp.port,
                    'game': resp.game,
                    'info': info
                })
        
        haloce_cache = {
            "count": {
                "players": total_players,
                "servers": len(server_list)
            },
            "updatedAt": get_current_http_date(),
            "servers": server_list
        }
        
        logger.info(f"Halo CE cache updated. Servers: {len(server_list)}, Players: {total_players}")
        
    except Exception as e:
        logger.error(f"Failed to update Halo CE cache: {e}")

async def update_halopc_cache():
    """Fetch Halo PC server list and update cache with summarized data."""
    global halopc_cache
    
    try:
        logger.info("Fetching Halo PC server list from master server...")

        servers = await _resolve_gamespy_servers(['pc'], timeout=5.0)
        
        if not servers:
            logger.warning("No Halo PC servers returned from master server")
            return
        
        logger.info(f"Found {len(servers)} Halo PC servers. Querying for details...")

        responses = await _query_gamespy_server_info(servers, timeout=2.0)

        server_list = []
        total_players = 0
        
        if responses:
            for resp in responses:
                info = _parse_gamespy_server_info(resp.data) if isinstance(resp.data, str) else {}
                
                player_count = info.get('numplayers', 0)
                if isinstance(player_count, int):
                    total_players += player_count
                
                server_list.append({
                    'address': resp.address,
                    'port': resp.port,
                    'game': resp.game,
                    'info': info
                })

        halopc_cache = {
            "count": {
                "players": total_players,
                "servers": len(server_list)
            },
            "updatedAt": get_current_http_date(),
            "servers": server_list
        }
        
        logger.info(f"Halo PC cache updated. Servers: {len(server_list)}, Players: {total_players}")
        
    except Exception as e:
        logger.error(f"Failed to update Halo PC cache: {e}")

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

# --- Background Task Loops ---

async def background_eldewrito_refresher():
    """Runs the update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_eldewrito_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

async def background_cartographer_refresher():
    """Runs the Cartographer update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_cartographer_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

async def background_haloce_refresher():
    """Runs the Halo CE update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_haloce_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

async def background_halopc_refresher():
    """Runs the Halo PC update logic every X seconds."""
    while True:
        start_time = datetime.now()
        await update_halopc_cache()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        sleep_time = max(0, REFRESH_INTERVAL - elapsed)
        await asyncio.sleep(sleep_time)

async def background_eldewrito_stats_recorder():
    """Records ElDewrito stats to database every 5 minutes."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        
        if eldewrito_cache and "count" in eldewrito_cache:
            player_count = eldewrito_cache["count"].get("players", 0)
            server_count = eldewrito_cache["count"].get("servers", 0)
            save_eldewrito_stats(player_count, server_count)

async def background_cartographer_stats_recorder():
    """Records Cartographer stats to database every 5 minutes."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        
        if cartographer_cache and "count" in cartographer_cache:
            player_count = cartographer_cache["count"].get("players", 0)
            server_count = cartographer_cache["count"].get("servers", 0)
            save_cartographer_stats(player_count, server_count)

async def background_haloce_stats_recorder():
    """Records Halo CE stats to database every 5 minutes."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        
        if haloce_cache and "count" in haloce_cache:
            player_count = haloce_cache["count"].get("players", 0)
            server_count = haloce_cache["count"].get("servers", 0)
            save_haloce_stats(player_count, server_count)

async def background_halopc_stats_recorder():
    """Records Halo PC stats to database every 5 minutes."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        
        if halopc_cache and "count" in halopc_cache:
            player_count = halopc_cache["count"].get("players", 0)
            server_count = halopc_cache["count"].get("servers", 0)
            save_halopc_stats(player_count, server_count)

# --- FastAPI Events & Routes ---

@app.on_event("startup")
async def startup_event():
    await init_db()

    # TODO: This could probably be handled a lot better (these async tasks have no kill condition)
    asyncio.create_task(background_eldewrito_refresher())
    asyncio.create_task(background_cartographer_refresher())
    asyncio.create_task(background_haloce_refresher())
    asyncio.create_task(background_halopc_refresher())
    asyncio.create_task(background_eldewrito_stats_recorder())
    asyncio.create_task(background_cartographer_stats_recorder())
    asyncio.create_task(background_haloce_stats_recorder())
    asyncio.create_task(background_halopc_stats_recorder())

# --- ElDewrito FastAPI Routes ---

@app.get("/api/")
async def get_eldewrito_servers():
    """Serve the current cached ElDewrito server data."""
    if not eldewrito_cache:
        return JSONResponse(
            status_code=503, 
            content={"error": "ElDewrito data is warming up, please try again in a few seconds."}
        )
    return eldewrito_cache

@app.get("/api/stats")
async def get_eldewrito_historical_stats():
    """Serve historical ElDewrito stats data for charting."""
    stats = get_eldewrito_stats_history()
    return stats

@app.get("/api/servicerecord")
async def get_eldewrito_service_record(uid: Optional[str] = None):
    """GET proxy: accept ?uid=... from address bar and forward to eldewrito API."""
    try:
        if not uid:
            return JSONResponse(status_code=400, content={"error": "Missing or invalid uid"})

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json", "User-Agent": "ElDewrito/0.7.1"}
            resp = await client.post("https://api.eldewrito.org/api/servicerecord", json={"uid": uid}, headers=headers, timeout=API_TIMEOUT)

            try:
                content = resp.json()
            except Exception:
                content = resp.text

            try:
                player_id = None
                if isinstance(content, dict):
                    id_val = content.get('id')
                    if not id_val and isinstance(content.get('player'), dict):
                        id_val = content['player'].get('id')

                    if id_val is not None and (isinstance(id_val, int) or (isinstance(id_val, str) and str(id_val).isdigit())):
                        player_id = str(id_val)

                if player_id:
                    stats_url = f"https://stats.eldewrito.org/player/{player_id}"
                    try:
                        stats_resp = await client.get(stats_url, timeout=API_TIMEOUT)
                        if stats_resp.status_code == 200 and stats_resp.text:
                            m = re.search(r"<span[^>]*class=[\"']playerRank[\"'][^>]*>\s*Rank:\s*(\d+)", stats_resp.text, re.IGNORECASE)
                            if m:
                                rank_val = int(m.group(1))
                                if isinstance(content, dict):
                                    content['rank'] = rank_val
                                else:
                                    content = {"raw": content, "rank": rank_val}
                    except Exception:
                        logger.debug("Failed to fetch or parse stats page for player id %s", player_id)
            except Exception:
                logger.debug("Error while attempting to enrich service record with player rank", exc_info=True)

            return JSONResponse(status_code=resp.status_code, content=content)
    except Exception as e:
        logger.exception("Error proxying GET service record request")
        return JSONResponse(status_code=503, content={"error": "Failed to fetch service record", "message": str(e)})

# --- Cartographer FastAPI Routes ---

@app.get("/api/cartographer")
async def get_cartographer_servers():
    """Serve the current Cartographer server list (summarized)."""
    if not cartographer_summarized_cache:
        return JSONResponse(
            status_code=503,
            content={"error": "Cartographer data is warming up, please try again in a few seconds."}
        )
    return cartographer_summarized_cache

@app.get("/api/cartographer/stats")
async def get_cartographer_historical_stats():
    """Serve historical Cartographer stats data for charting."""
    stats = get_cartographer_stats_history()
    return stats

@app.get("/api/cartographer/server/{server_id}")
async def get_cartographer_server_detail(server_id: str):
    """Fetch and return details for a specific Cartographer server."""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            server_data = await fetch_cartographer_server_details(client, server_id)
            if server_data:
                return server_data
            return JSONResponse(
                status_code=404,
                content={"error": "Server not found"}
            )
    except Exception as e:
        logger.error(f"Failed to fetch Cartographer server {server_id}: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "Failed to fetch server details", "message": str(e)}
        )

# --- Halo CE FastAPI Routes ---

@app.get("/api/haloce")
async def get_haloce_servers():
    """Serve the current cached Halo CE server data."""
    if not haloce_cache:
        return JSONResponse(
            status_code=503, 
            content={"error": "Halo CE data is warming up, please try again in a few seconds."}
        )
    return haloce_cache

@app.get("/api/haloce/stats")
async def get_haloce_historical_stats():
    """Serve historical Halo CE stats data for charting."""
    stats = get_haloce_stats_history()
    return stats

# --- Halo PC FastAPI Routes ---

@app.get("/api/halopc")
async def get_haloce_servers():
    """Serve the current cached Halo PC server data."""
    if not halopc_cache:
        return JSONResponse(
            status_code=503, 
            content={"error": "Halo CE data is warming up, please try again in a few seconds."}
        )
    return halopc_cache

@app.get("/api/halopc/stats")
async def get_haloce_historical_stats():
    """Serve historical Halo PC stats data for charting."""
    stats = get_halopc_stats_history()
    return stats

# --- Entry Point ---

if __name__ == "__main__":
    # In production, you would run this via command line: uvicorn server:app --host 0.0.0.0 --port 80
    uvicorn.run(app, host="0.0.0.0", port=8000)