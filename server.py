"""
ZekBrowser server poller.

A small FastAPI service that polls the ElDewrito master servers, cartographer.online
and the GameSpy master server (Halo CE / Halo PC), keeps the latest results in memory,
and records player/server counts to the shared SQLite database every few minutes.

Laravel proxies the public /api/* routes to this process on 127.0.0.1:8001.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import socket
import sqlite3
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Any, Awaitable, Callable, Optional

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# --- Configuration ---------------------------------------------------------

REFRESH_INTERVAL = float(os.environ.get("ZEK_REFRESH_INTERVAL", "15"))  # seconds between list refreshes
STATS_INTERVAL = float(os.environ.get("ZEK_STATS_INTERVAL", "300"))     # seconds between history samples
API_TIMEOUT = 5.0                                                        # seconds, per game-server request
DB_PATH = os.environ.get("ZEK_DB_PATH", "database/database.sqlite")

ELDEWRITO_MASTER_LIST = "dewrito.json"
ELDEWRITO_SERVICE_RECORD_URL = "https://api.eldewrito.org/api/servicerecord"
ELDEWRITO_STATS_PLAYER_URL = "https://stats.eldewrito.org/player/{player_id}"
LEGACY_ELDEWRITO_STATS_URL = "https://eldewrito.pauwlo.com/api/stats"

CARTOGRAPHER_BASE = "https://cartographer.online"
CARTOGRAPHER_LIST_URL = f"{CARTOGRAPHER_BASE}/live/server_list.php"
CARTOGRAPHER_SERVER_URL = f"{CARTOGRAPHER_BASE}/live/servers"
CARTOGRAPHER_WORKERS = 16

GAMESPY_MASTER_HOST = "hosthpc.com"
GAMESPY_MASTER_PORT = 28910

# History tables, one per game. Laravel's migrations own the schema; the
# CREATE TABLE IF NOT EXISTS below only matters when this runs stand-alone.
STATS_TABLES = {
    "eldewrito": "server_stats",
    "cartographer": "cartographer_stats",
    "haloce": "haloce_stats",
    "halopc": "halopc_stats",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("zekbrowser")

# --- Cartographer lookup tables ---------------------------------------------

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

# --- GameSpy protocol (Halo CE / Halo PC) -----------------------------------

# Short game name used in our API -> (GameSpy game id, GameSpy encryption key)
GAMESPY_GAMES = {
    "ce": ("halom", "e4Rd9J"),
    "pc": ("halor", "e4Rd9J"),
    "trial": ("halod", "yG3d9w"),
    "mac": ("halomac", "e4Rd9J"),
    "macdemo": ("halomacd", "e4Rd9J"),
    "beta": ("halo", "QW88cv"),
}

GAMESPY_IP_PORT_LENGTH = 6


class GameSpyFlags:
    A, B, C, D = 0x02, 0x08, 0x10, 0x20


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
    data: str


# enctypeX decryption, ported from Luigi Auriemma's gsmsalg / enctypex_decoder.
def _enctypex_func5(encxkey: bytearray, cnt: int, id_bytes: bytes, idlen: int, n1: int, n2: int) -> tuple[int, int, int]:
    if cnt == 0:
        return 0, n1, n2
    mask = 1
    if cnt > 1:
        while mask < cnt:
            mask = (mask << 1) + 1
    i = 0
    while True:
        n1 = encxkey[n1 & 0xFF] + id_bytes[n2]
        n2 += 1
        if n2 >= idlen:
            n2 = 0
            n1 += idlen
        tmp = n1 & mask
        i += 1
        if i > 11:
            tmp %= cnt
        if tmp <= cnt:
            break
    return tmp, n1, n2


def _enctypex_func4(encxkey: bytearray, id_bytes: bytes, idlen: int) -> None:
    if idlen < 1:
        return
    for i in range(256):
        encxkey[i] = i
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
    encxkey[260] = encxkey[n1 & 0xFF]


def _enctypex_func7(encxkey: bytearray, d: int) -> int:
    a = encxkey[256]
    b = encxkey[257]
    c = encxkey[a]
    encxkey[256] = (a + 1) & 0xFF
    encxkey[257] = (b + c) & 0xFF
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
    b = (b + a) & 0xFF
    encxkey[258] = b
    a = b
    c = encxkey[c]
    b = encxkey[257]
    b = encxkey[b]
    a = encxkey[a]
    c = (c + b) & 0xFF
    b = encxkey[260]
    b = encxkey[b]
    c = (c + b) & 0xFF
    b = encxkey[c]
    c = encxkey[256]
    c = encxkey[c]
    a = (a + c) & 0xFF
    c = encxkey[b]
    b = encxkey[a]
    encxkey[260] = d & 0xFF
    c = c ^ b ^ (d & 0xFF)
    encxkey[259] = c & 0xFF
    return c & 0xFF


def _enctypex_funcx(encxkey: bytearray, key: bytes, encxvalidate: bytearray, data: bytes, datalen: int) -> None:
    keylen = len(key)
    for i in range(datalen):
        idx1 = (key[i % keylen] * i) & 7
        idx2 = i & 7
        encxvalidate[idx1] = (encxvalidate[idx1] ^ encxvalidate[idx2] ^ data[i]) & 0xFF
    _enctypex_func4(encxkey, bytes(encxvalidate), 8)


def _enctypex_decoder(key: bytes, validate: bytes, data: bytes) -> Optional[bytes]:
    encxkey = bytearray(261)
    datalen = len(data)
    if datalen < 1:
        return None
    a = (data[0] ^ 0xEC) + 2
    if datalen < a:
        return None
    b = data[a - 1] ^ 0xEA
    if datalen < (a + b):
        return None
    encxvalidate = bytearray(validate[:8])
    _enctypex_funcx(encxkey, key, encxvalidate, bytes(data[a:a + b]), b)
    payload = bytearray(data[a + b:])
    for i in range(len(payload)):
        payload[i] = _enctypex_func7(encxkey, payload[i])
    return bytes(payload)


def _gamespy_decrypt(key: str, validate: str, data: bytes) -> Optional[bytes]:
    try:
        return _enctypex_decoder(key.encode("ascii"), validate.encode("ascii"), data)
    except Exception:
        logger.debug("GameSpy decryption failed", exc_info=True)
        return None


def _make_validation_key() -> str:
    return format(int(time.time() * 1000), "x")[-8:].zfill(8)


def _encode_master_server_request(game: str, validation_key: str) -> bytes:
    def cstring(s: str) -> list[int]:
        return [ord(c) for c in s] + [0]

    data = [0, 0, 0] + [1, 3, 0, 0, 0, 0] + cstring(game) + cstring(game) + cstring(validation_key) + [0] * 5
    data[1] = len(data)
    return bytes(data)


def _decode_master_server_response(data: bytes) -> list[tuple[str, int]]:
    """Returns the (ip, port) pairs contained in a decrypted master server reply."""
    if len(data) < GAMESPY_IP_PORT_LENGTH:
        return []
    scanner = GAMESPY_IP_PORT_LENGTH
    common_port = (data[4] << 8) | data[5]
    if common_port == 0xFFFF:
        return []

    def skip_pascal_string(offset: int) -> int:
        if offset >= len(data):
            return offset
        return offset + data[offset] + 1

    scanner = skip_pascal_string(scanner)
    scanner = skip_pascal_string(scanner)

    servers: list[tuple[str, int]] = []
    while scanner < len(data):
        flag = data[scanner]
        scanner += 1
        extra_len = sum([
            3 if flag & GameSpyFlags.A else 0,
            4 if flag & GameSpyFlags.B else 0,
            2 if flag & GameSpyFlags.C else 0,
            2 if flag & GameSpyFlags.D else 0,
        ])
        if scanner + GAMESPY_IP_PORT_LENGTH > len(data):
            break
        ip = ".".join(str(b) for b in data[scanner:scanner + 4])
        port = (data[scanner + 4] << 8) | data[scanner + 5]
        scanner += GAMESPY_IP_PORT_LENGTH + extra_len - 1
        if flag == 0 and ip == "255.255.255.255":
            break
        servers.append((ip, port))
    return servers


def _tcp_request(host: str, port: int, payload: bytes, timeout: float) -> bytes:
    """Blocking: send one request and read until the peer stops sending."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(payload)
        sock.settimeout(1.0)
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            response += chunk
        return response


async def _gamespy_master_server_list(game: str, timeout: float = 5.0) -> list[GameSpyServer]:
    """Ask the GameSpy master server for every registered server of a game ("ce", "pc", ...)."""
    spec = GAMESPY_GAMES.get(game.lower())
    if spec is None:
        return []
    game_id, key = spec
    try:
        vkey = _make_validation_key()
        request = _encode_master_server_request(game_id, vkey)
        encrypted = await asyncio.to_thread(_tcp_request, GAMESPY_MASTER_HOST, GAMESPY_MASTER_PORT, request, timeout)
        decrypted = _gamespy_decrypt(key, vkey, encrypted)
        if not decrypted:
            return []
        return [GameSpyServer(ip, port, game) for ip, port in _decode_master_server_response(decrypted)]
    except Exception as e:
        logger.warning("GameSpy master server query for %s failed: %s", game, repr(e))
        return []


def _udp_broadcast_and_collect(servers: list[GameSpyServer], end_delay: float) -> list[tuple[str, int, bytes]]:
    """Blocking: send a status query to every server, then collect replies until they stop arriving."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    responses: list[tuple[str, int, bytes]] = []
    try:
        for s in servers:
            try:
                sock.sendto(b"\\", (s.address, s.port))
            except OSError:
                continue
        time.sleep(0.2)
        last_receive = time.time()
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                responses.append((addr[0], addr[1], data))
                last_receive = time.time()
            except socket.timeout:
                if time.time() - last_receive > end_delay:
                    break
            except OSError:
                break
    finally:
        sock.close()
    return responses


async def _query_gamespy_servers(servers: list[GameSpyServer], timeout: float = 2.0) -> list[GameSpyServerResponse]:
    if not servers:
        return []
    game_by_address = {f"{s.address}:{s.port}": s.game for s in servers}
    raw = await asyncio.to_thread(_udp_broadcast_and_collect, servers, timeout)
    return [
        GameSpyServerResponse(ip, port, game_by_address.get(f"{ip}:{port}"), data.decode("utf-8", errors="ignore"))
        for ip, port, data in raw
    ]


def _clean_gamespy_string(s: str) -> str:
    result = []
    i = 0
    while i < len(s):
        c = s[i]
        if ord(c) < 32 and c not in "\t\n\r":
            i += 1
            continue
        if c == "^" and i + 1 < len(s) and (s[i + 1].isdigit() or s[i + 1].islower()):
            i += 2
            continue
        if c == "\\":
            result.append("/")
            i += 1
            continue
        if 32 <= ord(c) < 127 or ord(c) >= 128:
            result.append(c)
        i += 1
    return "".join(result)


def _parse_gamespy_server_info(response_str: str) -> dict[str, Any]:
    parts = response_str.split("\\")
    if parts and parts[0] == "":
        parts = parts[1:]
    info: dict[str, Any] = {}
    for i in range(0, len(parts) - 1, 2):
        key = parts[i]
        value: Any = _clean_gamespy_string(parts[i + 1])
        if value.isdigit():
            value = int(value)
        elif re.match(r"^\d+\.\d+$", value):
            value = float(value)
        info[key] = value
    return info

# --- Cartographer helpers ---------------------------------------------------


def clean_string_field(s: Any) -> Any:
    """Strip wrapping quotes and control characters from a Cartographer string value."""
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s.startswith('"'):
        s = s[1:]
    if s.endswith('"'):
        s = s[:-1]
    s = "".join(c for c in s if ord(c) >= 0x20 and ord(c) != 0x7F)
    return s.strip()


def decode_properties(pp: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn the pProperties array into named fields; the raw list is kept under '_raw'."""
    out: dict[str, Any] = {}
    raw_props = []
    for prop in pp:
        pid = prop.get("dwPropertyId")
        ptype = prop.get("type")
        val = clean_string_field(prop.get("value"))
        name = PROPERTY_MAP.get(pid)
        out_key = name if name else f"prop_{hex(pid) if isinstance(pid, int) else pid}"
        out[out_key] = {"value": val, "type": ptype}
        raw_props.append({"dwPropertyId": pid, "type": ptype, "value": val})
    out["_raw"] = raw_props
    return out


def _prop(decoded: dict[str, Any], name: str) -> Any:
    entry = decoded.get(name)
    return entry.get("value") if isinstance(entry, dict) else None


def summarize_server(data: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Reduce a raw Cartographer server document to the fields the browser shows."""
    if data is None:
        return {}

    decoded = decode_properties(data.get("pProperties") or [])

    server_name = (_prop(decoded, "server_name") or _prop(decoded, "prop_0x40008230") or "").strip()
    map_name = _prop(decoded, "map_name") or _prop(decoded, "map_name_2") or ""
    map_id = _prop(decoded, "map_id") or _prop(decoded, "map_id_2")
    variant = _prop(decoded, "gametype_name") or _prop(decoded, "gametype_name_2") or ""
    description = (_prop(decoded, "server_desc") or "").strip()

    gametype = ""
    gtid_raw = _prop(decoded, "gametype_id")
    if gtid_raw is not None:
        try:
            gametype = GAMETYPE_ID_TO_NAME.get(int(gtid_raw), str(int(gtid_raw)))
        except (TypeError, ValueError):
            gametype = str(gtid_raw)

    if not map_name and map_id is not None:
        try:
            mid = int(map_id)
            info = MAP_ID_TO_INFO.get(mid)
            map_name = info[1] if info else f"<map id {mid}>"
        except (TypeError, ValueError):
            map_name = f"<map id {map_id}>"

    summary: dict[str, Any] = {
        "xuid": data.get("xuid") or data.get("XUID") or None,
        "players": {"filled": data.get("dwFilledPublicSlots"), "max": data.get("dwMaxPublicSlots")},
        "server_name": server_name,
        "map_name": map_name,
        "map_id": map_id,
        "gametype": gametype,
        "variant": variant,
        "description": description,
        "decoded_properties": decoded,
    }
    # Raw network fields that are not part of the property list but useful for debugging.
    for key in ("saddr", "abenet", "abonline", "xnaddr"):
        if key in data:
            summary[key] = data.get(key)
    return summary


def _failed_cartographer_server(server_id: Any) -> dict[str, Any]:
    return {"xuid": server_id, "server_name": "", "map_name": "", "gametype": "", "variant": "", "description": "<failed>"}


async def fetch_cartographer_server_details(client: httpx.AsyncClient, server_id: Any) -> dict[str, Any]:
    try:
        r = await client.get(f"{CARTOGRAPHER_SERVER_URL}/{server_id}", timeout=15.0)
        r.raise_for_status()
        json_data = r.json()
        summary = summarize_server(json_data)
        if not summary:
            logger.warning("Cartographer server %s returned empty data", server_id)
            return _failed_cartographer_server(server_id)
        summary["_raw_cartographer"] = json_data
        return summary
    except Exception as e:
        logger.warning("Failed to fetch Cartographer server %s: %s", server_id, e)
        return _failed_cartographer_server(server_id)

# --- Database ---------------------------------------------------------------


def _db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _db_timestamp(dt: datetime) -> str:
    """ISO-8601 with a space separator, the same text format the old implicit adapter produced."""
    return dt.isoformat(sep=" ")


def init_db() -> int:
    """Create the history tables when missing; returns the ElDewrito row count."""
    with _db() as conn:
        for table in STATS_TABLES.values():
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_count INTEGER NOT NULL DEFAULT 0,
                    server_count INTEGER NOT NULL DEFAULT 0,
                    recorded_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_recorded_at ON {table}(recorded_at)")
        row = conn.execute(f"SELECT COUNT(*) FROM {STATS_TABLES['eldewrito']}").fetchone()
    logger.info("Database initialized")
    return int(row[0]) if row else 0


def save_stats(game: str, player_count: int, server_count: int) -> None:
    table = STATS_TABLES[game]
    try:
        with _db() as conn:
            conn.execute(
                f"INSERT INTO {table} (player_count, server_count, recorded_at) VALUES (?, ?, ?)",
                (player_count, server_count, _db_timestamp(datetime.now(timezone.utc))),
            )
        logger.info("Saved %s stats: %d servers, %d players", game, server_count, player_count)
    except Exception as e:
        logger.error("Failed to save %s stats: %s", game, e)


def get_stats_history(game: str) -> dict[str, list[list[int]]]:
    """Highcharts-style [[timestampMs, value], ...] series for players and servers."""
    table = STATS_TABLES[game]
    try:
        with _db() as conn:
            rows = conn.execute(f"""
                SELECT CAST(strftime('%s', recorded_at) AS INTEGER) * 1000, player_count, server_count
                FROM {table}
                ORDER BY recorded_at ASC
            """).fetchall()
        return {
            "players": [[row[0], row[1]] for row in rows],
            "servers": [[row[0], row[2]] for row in rows],
        }
    except Exception as e:
        logger.error("Failed to retrieve %s stats: %s", game, e)
        return {"players": [], "servers": []}


async def import_legacy_eldewrito_stats() -> None:
    """One-time import of the historical ElDewrito chart data from pauwlo's API."""
    try:
        async with httpx.AsyncClient() as client:
            logger.info("Fetching legacy ElDewrito stats from %s...", LEGACY_ELDEWRITO_STATS_URL)
            response = await client.get(LEGACY_ELDEWRITO_STATS_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.warning("Failed to fetch legacy ElDewrito stats: %s", e)
        return

    players = data.get("players") if isinstance(data, dict) else None
    servers = data.get("servers") if isinstance(data, dict) else None
    if not isinstance(players, list) or not isinstance(servers, list):
        logger.warning("Legacy stats API returned unexpected format")
        return
    if not players and not servers:
        logger.info("No legacy data available, starting with an empty ElDewrito history")
        return

    players_by_ts = {entry[0]: entry[1] for entry in players}
    servers_by_ts = {entry[0]: entry[1] for entry in servers}
    rows = [
        (
            players_by_ts.get(ts, 0),
            servers_by_ts.get(ts, 0),
            _db_timestamp(datetime.fromtimestamp(ts / 1000, tz=timezone.utc)),
        )
        for ts in sorted(set(players_by_ts) | set(servers_by_ts))
    ]
    try:
        with _db() as conn:
            conn.executemany(
                f"INSERT INTO {STATS_TABLES['eldewrito']} (player_count, server_count, recorded_at) VALUES (?, ?, ?)",
                rows,
            )
        logger.info("Imported %d historical ElDewrito records", len(rows))
    except Exception as e:
        logger.error("Failed to import legacy ElDewrito stats: %s", e)

# --- Shared helpers ---------------------------------------------------------


def http_date_now() -> str:
    """Current time as an RFC 1123 HTTP date (the format the ElDewrito browser expects)."""
    return formatdate(timeval=None, localtime=False, usegmt=True)


def make_cache(servers: Any, player_count: int, server_count: int) -> dict[str, Any]:
    return {
        "count": {"players": player_count, "servers": server_count},
        "updatedAt": http_date_now(),
        "servers": servers,
    }


async def resolve_reverse_dns(ip: str) -> Optional[str]:
    try:
        host_info = await asyncio.to_thread(socket.gethostbyaddr, ip)
        return host_info[0]
    except Exception:
        return None

# --- ElDewrito --------------------------------------------------------------


def load_eldewrito_master_urls() -> list[str]:
    with open(ELDEWRITO_MASTER_LIST, "r", encoding="utf-8") as f:
        config = json.load(f)
    return [m["list"] for m in config.get("masterServers", []) if "list" in m]


async def fetch_master_list(client: httpx.AsyncClient, url: str) -> list[str]:
    """Queries one master server and returns its "ip:port" strings."""
    try:
        response = await client.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        servers = data.get("result", {}).get("servers") if isinstance(data, dict) else None
        return [s for s in servers if isinstance(s, str)] if isinstance(servers, list) else []
    except Exception as e:
        # httpx timeouts stringify to "", so include the exception type.
        logger.warning("Failed to query master server %s: %s", url, repr(e))
        return []


async def fetch_server_mods(client: httpx.AsyncClient, ip_port: str) -> Optional[dict[str, Any]]:
    try:
        response = await client.get(f"http://{ip_port}/mods", timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug("Failed to fetch mods from %s: %s", ip_port, e)
        return None


async def fetch_game_server_info(client: httpx.AsyncClient, ip_port: str) -> Optional[tuple[str, dict[str, Any]]]:
    """Queries one ElDewrito game server's JSON endpoint and decorates the result."""
    try:
        response = await client.get(f"http://{ip_port}/", timeout=API_TIMEOUT)
        response.raise_for_status()
        server_data = response.json()
        if not isinstance(server_data, dict):
            return None

        rdns = await resolve_reverse_dns(ip_port.split(":")[0])
        if rdns:
            server_data["reverseDns"] = rdns

        # There is no persistence for first-seen; it is the time of this refresh.
        server_data["firstSeenAt"] = http_date_now()

        version_short = None
        if isinstance(server_data.get("eldewritoVersion"), str):
            version_short = server_data["eldewritoVersion"].split("-")[0]
            server_data["eldewritoVersionShort"] = version_short

        # The /mods endpoint exists from 0.7 on.
        if version_short and version_short.startswith("0.7"):
            mods_data = await fetch_server_mods(client, ip_port)
            if mods_data:
                server_data["mods"] = mods_data

        return ip_port, server_data
    except Exception as e:
        logger.debug("Failed to fetch server info from %s: %s", ip_port, e)
        return None


async def update_eldewrito_cache() -> Optional[dict[str, Any]]:
    try:
        master_urls = load_eldewrito_master_urls()
    except Exception as e:
        logger.error("Error reading %s: %s", ELDEWRITO_MASTER_LIST, e)
        return None

    async with httpx.AsyncClient() as client:
        logger.info("Querying %d ElDewrito master servers...", len(master_urls))
        results = await asyncio.gather(*(fetch_master_list(client, url) for url in master_urls))
        unique_servers = {ip_port for server_list in results for ip_port in server_list}

        logger.info("Found %d unique ElDewrito servers. Querying details...", len(unique_servers))
        game_results = await asyncio.gather(*(fetch_game_server_info(client, srv) for srv in unique_servers))

    servers: dict[str, dict[str, Any]] = {}
    total_players = 0
    for res in game_results:
        if not res:
            continue
        ip_port, data = res
        servers[ip_port] = data
        try:
            total_players += int(data.get("numPlayers", 0))
        except (TypeError, ValueError):
            pass

    logger.info("ElDewrito cache updated. Servers: %d, Players: %d", len(servers), total_players)
    return make_cache(servers, total_players, len(servers))

# --- Cartographer -----------------------------------------------------------


async def update_cartographer_cache() -> Optional[dict[str, Any]]:
    async with httpx.AsyncClient(verify=False) as client:
        logger.info("Fetching Cartographer server list...")
        response = await client.get(CARTOGRAPHER_LIST_URL, timeout=15.0)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            raw_list = data.get("servers", data.get("list", data.get("data", [])))
        else:
            raw_list = []

        # The list endpoint either embeds full server documents or only ids.
        embedded = []
        ids = []
        for item in raw_list:
            if isinstance(item, dict) and (item.get("pProperties") or item.get("server_desc") or item.get("name")):
                embedded.append(summarize_server(item))
            else:
                ids.append(item)

        if embedded:
            logger.info("Using pre-summarized Cartographer data (%d servers)", len(embedded))
            servers = embedded
        else:
            logger.info("Fetching details for %d Cartographer servers...", len(ids))
            sem = asyncio.Semaphore(CARTOGRAPHER_WORKERS)

            async def fetch_one(sid: Any) -> dict[str, Any]:
                async with sem:
                    return await fetch_cartographer_server_details(client, sid)

            servers = list(await asyncio.gather(*(fetch_one(sid) for sid in ids)))

    total_players = 0
    for server in servers:
        players = server.get("players") if isinstance(server, dict) else None
        if isinstance(players, dict):
            try:
                total_players += int(players.get("filled") or 0)
            except (TypeError, ValueError):
                pass

    logger.info("Cartographer cache updated. Servers: %d, Players: %d", len(servers), total_players)
    return make_cache(servers, total_players, len(servers))

# --- Halo CE / Halo PC (GameSpy) -------------------------------------------


async def update_gamespy_cache(game: str, label: str) -> Optional[dict[str, Any]]:
    logger.info("Fetching %s server list from master server...", label)
    servers = await _gamespy_master_server_list(game, timeout=5.0)
    if not servers:
        logger.warning("No %s servers returned from master server", label)
        return None

    logger.info("Found %d %s servers. Querying for details...", len(servers), label)
    responses = await _query_gamespy_servers(servers, timeout=2.0)

    server_list = []
    total_players = 0
    for resp in responses:
        info = _parse_gamespy_server_info(resp.data)
        player_count = info.get("numplayers", 0)
        if isinstance(player_count, int):
            total_players += player_count
        server_list.append({"address": resp.address, "port": resp.port, "game": resp.game, "info": info})

    logger.info("%s cache updated. Servers: %d, Players: %d", label, len(server_list), total_players)
    return make_cache(server_list, total_players, len(server_list))

# --- Background loops -------------------------------------------------------

caches: dict[str, dict[str, Any]] = {name: {} for name in STATS_TABLES}

Updater = Callable[[], Awaitable[Optional[dict[str, Any]]]]

UPDATERS: dict[str, tuple[str, Updater]] = {
    "eldewrito": ("ElDewrito", update_eldewrito_cache),
    "cartographer": ("Cartographer", update_cartographer_cache),
    "haloce": ("Halo CE", lambda: update_gamespy_cache("ce", "Halo CE")),
    "halopc": ("Halo PC", lambda: update_gamespy_cache("pc", "Halo PC")),
}


async def refresh_loop(name: str) -> None:
    """Refresh one game's cache every REFRESH_INTERVAL seconds; a failed refresh keeps the old data."""
    label, update = UPDATERS[name]
    while True:
        started = time.monotonic()
        try:
            result = await update()
            if result is not None:
                caches[name] = result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Failed to update %s cache: %s", label, e)
        await asyncio.sleep(max(0.0, REFRESH_INTERVAL - (time.monotonic() - started)))


async def stats_loop(name: str) -> None:
    """Sample one game's player/server counts into its history table every STATS_INTERVAL seconds."""
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        count = caches[name].get("count")
        if isinstance(count, dict):
            save_stats(name, int(count.get("players", 0)), int(count.get("servers", 0)))


@asynccontextmanager
async def lifespan(_: FastAPI):
    if init_db() == 0:
        logger.info("ElDewrito stats table is empty, attempting to fetch legacy data...")
        await import_legacy_eldewrito_stats()

    tasks = [asyncio.create_task(refresh_loop(name), name=f"refresh:{name}") for name in UPDATERS]
    tasks += [asyncio.create_task(stats_loop(name), name=f"stats:{name}") for name in UPDATERS]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)

# --- Routes -----------------------------------------------------------------


def cached_list(name: str, label: str):
    cache = caches[name]
    if not cache:
        return JSONResponse(status_code=503, content={"error": f"{label} data is warming up, please try again in a few seconds."})
    return cache


@app.get("/api/")
async def get_eldewrito_servers():
    return cached_list("eldewrito", "ElDewrito")


@app.get("/api/stats")
async def get_eldewrito_stats():
    return get_stats_history("eldewrito")


@app.get("/api/cartographer")
async def get_cartographer_servers():
    return cached_list("cartographer", "Cartographer")


@app.get("/api/cartographer/stats")
async def get_cartographer_stats():
    return get_stats_history("cartographer")


@app.get("/api/cartographer/server/{server_id}")
async def get_cartographer_server_detail(server_id: str):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            return await fetch_cartographer_server_details(client, server_id)
    except Exception as e:
        logger.error("Failed to fetch Cartographer server %s: %s", server_id, e)
        return JSONResponse(status_code=503, content={"error": "Failed to fetch server details", "message": str(e)})


@app.get("/api/haloce")
async def get_haloce_servers():
    return cached_list("haloce", "Halo CE")


@app.get("/api/haloce/stats")
async def get_haloce_stats():
    return get_stats_history("haloce")


@app.get("/api/halopc")
async def get_halopc_servers():
    return cached_list("halopc", "Halo PC")


@app.get("/api/halopc/stats")
async def get_halopc_stats():
    return get_stats_history("halopc")


def _extract_player_id(content: Any) -> Optional[str]:
    if not isinstance(content, dict):
        return None
    id_val = content.get("id")
    if not id_val and isinstance(content.get("player"), dict):
        id_val = content["player"].get("id")
    if isinstance(id_val, int) or (isinstance(id_val, str) and id_val.isdigit()):
        return str(id_val)
    return None


async def _fetch_player_rank(client: httpx.AsyncClient, player_id: str) -> Optional[int]:
    """Scrape the rank from the stats.eldewrito.org player page (there is no JSON API for it)."""
    try:
        resp = await client.get(ELDEWRITO_STATS_PLAYER_URL.format(player_id=player_id), timeout=API_TIMEOUT)
        if resp.status_code != 200 or not resp.text:
            return None
        m = re.search(r"<span[^>]*class=[\"']playerRank[\"'][^>]*>\s*Rank:\s*(\d+)", resp.text, re.IGNORECASE)
        return int(m.group(1)) if m else None
    except Exception:
        logger.debug("Failed to fetch or parse stats page for player id %s", player_id)
        return None


@app.get("/api/servicerecord")
async def get_eldewrito_service_record(uid: Optional[str] = None):
    """Forward ?uid=... to the ElDewrito service record API and enrich the reply with the player's rank."""
    if not uid:
        return JSONResponse(status_code=400, content={"error": "Missing or invalid uid"})
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json", "User-Agent": "ElDewrito/0.7.1"}
            resp = await client.post(ELDEWRITO_SERVICE_RECORD_URL, json={"uid": uid}, headers=headers, timeout=API_TIMEOUT)
            try:
                content: Any = resp.json()
            except ValueError:
                content = resp.text

            player_id = _extract_player_id(content)
            if player_id:
                rank = await _fetch_player_rank(client, player_id)
                if rank is not None:
                    if isinstance(content, dict):
                        content["rank"] = rank
                    else:
                        content = {"raw": content, "rank": rank}

            return JSONResponse(status_code=resp.status_code, content=content)
    except Exception as e:
        logger.exception("Error proxying service record request")
        return JSONResponse(status_code=503, content={"error": "Failed to fetch service record", "message": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
