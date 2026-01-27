#!/usr/bin/env python3
import asyncio
import httpx
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

BASE = "https://cartographer.online"
LIST_URL = f"{BASE}/live/server_list.php"
TIMEOUT = 15.0
WORKERS = 16

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


def clean_string_field(s: Any) -> Any:
    if not isinstance(s, str):
        return s
    s = s.strip()
    # remove wrapping quotes
    # remove a single leading or trailing double-quote if present
    if s.startswith('"'):
        s = s[1:]
    if s.endswith('"'):
        s = s[:-1]
    # preserve raw unicode exactly (do not unescape escape sequences)
    # strip control chars but keep all other unicode
    s = ''.join(c for c in s if ord(c) >= 0x20 and ord(c) != 0x7f)
    return s.strip()


def decode_pproperties(pp: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    if data is None:
        return {}
    summary = {}
    summary['xuid'] = data.get('xuid') or data.get('XUID') or None
    summary['players'] = { 'filled': data.get('dwFilledPublicSlots'), 'max': data.get('dwMaxPublicSlots') }
    pp = data.get('pProperties') or []
    decoded = decode_pproperties(pp)

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
    summary['_decoded_properties'] = decoded
    return summary


async def fetch_server_details(client: httpx.AsyncClient, server_id: Any) -> Optional[Dict[str, Any]]:
    url = f"{BASE}/live/servers/{server_id}"
    try:
        r = await client.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return summarize_server(r.json())
    except Exception as e:
        # return a minimal record indicating failure
        return {'xuid': server_id, 'server_name': '', 'map_name': '', 'gametype': '', 'variant': '', 'description': '<failed>'}


async def main():
    async with httpx.AsyncClient(verify=False) as client:
        r = await client.get(LIST_URL, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            for key in ('servers','list','data'):
                if key in data and isinstance(data[key], list):
                    raw_list = data[key]
                    break
            else:
                raw_list = []
        else:
            raw_list = []

        # if raw_list contains server objects with pProperties, map them directly
        mapped = []
        ids = []
        for item in raw_list:
            if isinstance(item, dict) and (item.get('pProperties') or item.get('server_desc') or item.get('name')):
                mapped.append(summarize_server(item))
            else:
                ids.append(item)

        if mapped:
            print(json.dumps(mapped))
            return

        # otherwise fetch each server detail concurrently with limited concurrency
        sem = asyncio.Semaphore(WORKERS)
        async def sem_fetch(sid):
            async with sem:
                return await fetch_server_details(client, sid)

        tasks = [sem_fetch(sid) for sid in ids]
        results = await asyncio.gather(*tasks)
        print(json.dumps(results))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)
