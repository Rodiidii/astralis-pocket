from __future__ import annotations

import json
import os
import re
import threading
import time
import hashlib
import secrets
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlsplit, unquote, urlparse, quote, urlencode, urljoin

HOST = "0.0.0.0" if os.environ.get("RENDER") or os.environ.get("PORT") else "127.0.0.1"
PORT = int(os.environ.get("PORT", "8766"))
TTL = 900
cache: dict[str, tuple[float, bytes]] = {}
cache_lock = threading.Lock()
_HOYOLAB_RESIN_CACHE: tuple[float, dict] | None = None
_HOYOLAB_SECRET_MEMORY: dict | None = None

def _hoyolab_secret_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "Astralis"
    root.mkdir(parents=True, exist_ok=True)
    return root / "hoyolab.dpapi"

def _dpapi(data: bytes, protect: bool) -> bytes:
    """Encrypt/decrypt a small local secret with the current Windows user profile."""
    if os.name != "nt":
        raise RuntimeError("Le coffre HoYoLAB sécurisé requiert Windows DPAPI.")
    import ctypes
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
    source = ctypes.create_string_buffer(data)
    incoming = Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    outgoing = Blob()
    crypt = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if protect:
        ok = crypt(ctypes.byref(incoming), "Astralis HoYoLAB", None, None, None, 0x01, ctypes.byref(outgoing))
    else:
        ok = crypt(ctypes.byref(incoming), None, None, None, None, 0x01, ctypes.byref(outgoing))
    if not ok:
        raise OSError("Windows n’a pas pu ouvrir le coffre local DPAPI.")
    try:
        return ctypes.string_at(outgoing.pbData, outgoing.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(outgoing.pbData)

def _read_hoyolab_secret() -> dict | None:
    if os.name != "nt": return _HOYOLAB_SECRET_MEMORY
    path = _hoyolab_secret_path()
    if not path.exists(): return None
    return json.loads(_dpapi(path.read_bytes(), False).decode("utf-8"))

def _write_hoyolab_secret(data: dict | None) -> None:
    global _HOYOLAB_SECRET_MEMORY
    if os.name != "nt":
        _HOYOLAB_SECRET_MEMORY = data
        return
    path = _hoyolab_secret_path()
    if data is None:
        path.unlink(missing_ok=True)
        return
    path.write_bytes(_dpapi(json.dumps(data, ensure_ascii=False).encode("utf-8"), True))

def _fetch_hoyolab_resin() -> dict:
    global _HOYOLAB_RESIN_CACHE
    now = time.time()
    if _HOYOLAB_RESIN_CACHE and now - _HOYOLAB_RESIN_CACHE[0] < 60:
        return _HOYOLAB_RESIN_CACHE[1]
    auth = _read_hoyolab_secret()
    if not auth: raise LookupError("Configure la connexion HoYoLAB locale dans l’onglet HoYoLAB.")
    uid, region, cookie = auth["uid"], auth["region"], auth["cookie"]
    url = f"https://bbs-api-os.hoyolab.com/game_record/genshin/api/dailyNote?server={region}&role_id={uid}"
    timestamp, rand = str(int(now)), secrets.token_hex(4)
    query = f"server={region}&role_id={uid}"
    digest = hashlib.md5(f"salt=6s25p5ox5y14umn1p61aqyyvbvvl3lrt&t={timestamp}&r={rand}&b=&q={query}".encode()).hexdigest()
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36", "Accept":"application/json", "Referer":"https://act.hoyolab.com/", "Origin":"https://act.hoyolab.com", "x-rpc-app_version":"2.71.1", "x-rpc-client_type":"5", "x-rpc-language":"fr-fr", "DS":f"{timestamp},{rand},{digest}", "Cookie":cookie})
    with urlopen(req, timeout=18) as response: payload = json.loads(response.read())
    if payload.get("retcode") != 0:
        message = str(payload.get("message") or "")
        if "not public" in message.lower() or "non public" in message.lower():
            raise RuntimeError("HoYoLAB indique que ta Chronique de bataille est privée. Dans HoYoLAB, ouvre Compte → Ma Chronique de bataille et active l’option Public, puis vérifie que l’UID et le serveur Europe correspondent à ton compte Genshin.")
        if payload.get("retcode") in {10102, 10103}:
            raise RuntimeError("HoYoLAB ne peut pas lire cette Chronique de bataille. Rends-la publique dans HoYoLAB → Compte → Ma Chronique de bataille, puis vérifie l’UID et le serveur.")
        raise RuntimeError(message or "HoYoLAB a refusé la requête. Vérifie la session, le serveur et l’UID.")
    data = payload.get("data") or {}
    result = {"current":int(data.get("current_resin",0)),"maximum":int(data.get("max_resin",200)),"recoverySeconds":int(data.get("resin_recovery_time",0)),"updatedAt":now,"source":"HoYoLAB · Battle Chronicle"}
    _HOYOLAB_RESIN_CACHE = (now, result)
    return result

SOURCES = {
    ("hsr", "character"): "https://vizualabstract.github.io/StarRailStaticAPI/db/fr/characters.json",
    ("hsr", "weapon"): "https://vizualabstract.github.io/StarRailStaticAPI/db/fr/light_cones.json",
    ("hsr", "artifact"): "https://vizualabstract.github.io/StarRailStaticAPI/db/fr/relic_sets.json",
    ("hsr", "skills"): "https://vizualabstract.github.io/StarRailStaticAPI/db/fr/character_skills.json",
    ("gi", "character"): "https://genshin.jmp.blue/characters/all",
    ("gi", "weapon"): "https://genshin.jmp.blue/weapons/all",
    ("gi", "artifact"): "https://genshin.jmp.blue/artifacts/all",
}
WW_ROUTES = {"character": "characters", "weapon": "weapons", "artifact": "echos"}
BASE = "https://wutheringdb.com"
WW_ASSET_INDEX_URL = "https://api.github.com/repos/ryanbenson/wuthering-waves-assets/contents/images"
ww_asset_cache: tuple[float, dict[str, str]] | None = None
ENDGAME_URLS = ("https://genshinflex.com/en/abyss/", "https://genshinflex.com/en/theater/history/", "https://genshinflex.com/en/onslaught/")
LORE_INDEX_TTL = 86400
LORE_INDEX_CATEGORIES = (
    "Character Lore Histories", "Historical Events", "Historical Figures", "Lore",
    "Mythology", "Gods", "Archons", "Celestia", "Khaenri'ah", "Enkanomiya",
    "Organizations", "Locations", "Books", "Quests", "Teyvat",
)
gi_lore_index_cache: tuple[float, bytes] | None = None
GI_LORE_CACHE_FILE = Path(__file__).resolve().parent / ".cache" / "gi-lore-index-v3.json"


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Astralis/1.0)", "Accept": "application/json,text/html,*/*"})
    with urlopen(request, timeout=18) as response:
        return response.read()


_GI_ALIAS_CACHE: dict | None = None

def gi_name_aliases(kind: str, name: str) -> set[str]:
    """Resolve localized catalog labels to the English names used by public guide indexes."""
    global _GI_ALIAS_CACHE
    if _GI_ALIAS_CACHE is None:
        try: _GI_ALIAS_CACHE = json.loads((Path(__file__).resolve().parent / "public" / "gi-name-aliases.json").read_text(encoding="utf-8"))
        except Exception: _GI_ALIAS_CACHE = {}
    group = {"character":"characters", "weapon":"weapons", "artifact":"artifacts"}.get(kind, kind)
    token = re.sub(r"[^a-z0-9]+", "", name.casefold())
    aliases = {name}
    for row in (_GI_ALIAS_CACHE.get(group, []) if isinstance(_GI_ALIAS_CACHE, dict) else []):
        candidates = (row.get("fr", []) or []) + (row.get("en", []) or [])
        if any(re.sub(r"[^a-z0-9]+", "", str(candidate).casefold()) == token for candidate in candidates):
            aliases.update(str(candidate) for candidate in candidates if candidate)
            break
    return aliases

_GI_BUILD_REVERSE_CACHE: tuple[float, list[dict]] | None = None

def gi_build_reverse_index() -> list[dict]:
    """Index Genshin.gg's public build catalogue for weapon/artifact reverse lookup."""
    global _GI_BUILD_REVERSE_CACHE
    now = time.time()
    if _GI_BUILD_REVERSE_CACHE is None or now - _GI_BUILD_REVERSE_CACHE[0] > 21600:
        html = fetch("https://genshin.gg/builds/").decode("utf-8", "ignore")
        starts = list(re.finditer(r'<div class="builds-list-item">', html, re.I))
        rows = []
        for i, match in enumerate(starts):
            end = starts[i+1].start() if i+1 < len(starts) else len(html)
            body = html[match.start():end]
            name = re.search(r'<div class="build-name">(.*?)</div>', body, re.I | re.S)
            role = re.search(r'<div class="build-role">(.*?)</div>', body, re.I | re.S)
            if not name: continue
            image = re.search(r'<img\b[^>]*?(?:src|data-src)=["\']([^"\']+)', body, re.I | re.S)
            gear = [html_text(x) for x in re.findall(r'<div class="build-weapon-name">(.*?)</div>', body, re.I | re.S)]
            weapon = gear[0] if gear else ""
            sets = gear[1:]
            rows.append({"name": html_text(name.group(1)), "role": html_text(role.group(1)) if role else "", "weapon": weapon, "sets": sets, "icon": urljoin("https://genshin.gg/", unescape(image.group(1))) if image else "", "url": "https://genshin.gg" + (re.search(r'<a href="(/characters/[^"]+)', body, re.I).group(1) if re.search(r'<a href="(/characters/[^"]+)', body, re.I) else "")})
        _GI_BUILD_REVERSE_CACHE = (now, rows)
    return (_GI_BUILD_REVERSE_CACHE or (0, []))[1]

_GI_TEAM_GUIDE_CACHE: tuple[float, list[dict]] | None = None

def gi_team_recommendations(character_name: str) -> list[dict]:
    """Parse the public, image-backed Genshin.gg team index and keep its attribution."""
    global _GI_TEAM_GUIDE_CACHE
    now = time.time()
    if _GI_TEAM_GUIDE_CACHE is None or now - _GI_TEAM_GUIDE_CACHE[0] > 21600:
        html = fetch("https://genshin.gg/teams/").decode("utf-8", "ignore")
        headers = list(re.finditer(r'<h2 class="teams-section-title">(.*?)</h2>', html, re.I | re.S))
        starts = list(re.finditer(r'<div class="team-name">(.*?)</div>', html, re.I | re.S))
        teams = []
        for i, match in enumerate(starts):
            end = starts[i+1].start() if i+1 < len(starts) else len(html)
            segment = html[match.end():end]
            members = []
            for slot in re.finditer(r"<div class=[^>]*team-slot[^>]*>(.*?)(?=<div class=[^>]*team-slot|$)", segment, re.I | re.S):
                body = slot.group(1)
                name_match = re.search(r'<h2 class="character-name">(.*?)</h2>', body, re.I | re.S)
                icon_match = re.search(r'<img[^>]+class="character-icon[^"]*"[^>]+src="([^"]+)"', body, re.I)
                link_match = re.search(r'<a href="([^"]+)" class="character-portrait"', body, re.I)
                if name_match:
                    members.append({"name": html_text(name_match.group(1)), "icon": unescape(icon_match.group(1)) if icon_match else "", "url": urljoin("https://genshin.gg/", link_match.group(1)) if link_match else ""})
            if len(members) < 2: continue
            section = next((h.group(1) for h in reversed(headers) if h.start() < match.start()), "Teams")
            teams.append({"name": html_text(match.group(1)), "group": html_text(section), "members": members})
        _GI_TEAM_GUIDE_CACHE = (now, teams)
    normalized = re.sub(r"[^a-z0-9]+", "", character_name.casefold())
    matches = [team for team in (_GI_TEAM_GUIDE_CACHE or (0, []))[1] if any(re.sub(r"[^a-z0-9]+", "", member["name"].casefold()) == normalized for member in team["members"])]
    if matches: return matches[:8]
    # Genshin.gg's global team index is incomplete; its character pages contain
    # dedicated team blocks for characters absent from the index (e.g. Alhaitham).
    slug = re.sub(r"[^a-z0-9]+", "", character_name.casefold())
    profile_url = next((row.get("url") for row in gi_build_reverse_index() if re.sub(r"[^a-z0-9]+", "", row.get("name", "").casefold()) == normalized and row.get("url")), "")
    if not profile_url and slug: profile_url = f"https://genshin.gg/characters/{slug}/"
    if not profile_url: return []
    html = fetch(profile_url).decode("utf-8", "ignore")
    starts = list(re.finditer(r'<div class="character-team">', html, re.I))
    teams = []
    for i, match in enumerate(starts):
        end = starts[i+1].start() if i+1 < len(starts) else html.find('</div><h2 class="character-category">', match.start())
        if end < 0: end = len(html)
        block = html[match.start():end]
        title = re.search(r'<div class="character-team-name">(.*?)</div>', block, re.I | re.S)
        members = []
        for icon in re.finditer(r'<img[^>]*class="character-icon[^"]*"[^>]*>', block, re.I):
            tag = icon.group(0)
            name_match = re.search(r'\balt="([^"]+)"', tag, re.I)
            src_match = re.search(r'\bsrc="([^"]+)"', tag, re.I)
            if not name_match: continue
            before = block.rfind('<a ', 0, icon.start()); after = block.find('</a>', icon.end())
            link = re.search(r'\bhref="([^"]+)"', block[before:after] if before >= 0 and after >= 0 else '', re.I)
            members.append({"name": html_text(name_match.group(1)), "icon": unescape(src_match.group(1)) if src_match else "", "url": urljoin("https://genshin.gg/", link.group(1)) if link else ""})
        # The paired element icon uses another class; keep only the character-icon records.
        if len(members) >= 2:
            teams.append({"name": html_text(title.group(1)) if title else character_name + " · équipe recommandée", "group": "Équipe · fiche de personnage", "members": members[:4]})
    return teams[:8]

_GI_BUILDS_TREE: tuple[float, list[str]] | None = None

def gi_build_guide(character_slug: str) -> dict:
    """Return a compact, cached build guide from the community-maintained GIHT dataset."""
    global _GI_BUILDS_TREE
    slug = re.sub(r"[^a-z0-9-]+", "-", character_slug.casefold()).strip("-")
    if not slug or len(slug) > 64:
        raise ValueError("Nom de personnage invalide.")
    now = time.time()
    if _GI_BUILDS_TREE is None or now - _GI_BUILDS_TREE[0] > 21600:
        payload = json.loads(fetch("https://api.github.com/repos/Genshin-Impact-Helper-Team/genshin-builds/git/trees/main?recursive=1"))
        _GI_BUILDS_TREE = (now, [row["path"] for row in payload.get("tree", []) if row.get("type") == "blob" and row.get("path", "").startswith("src/content/")])
    paths = _GI_BUILDS_TREE[1]
    suffix = f"/{slug}/metadata.json"
    metadata_path = next((p for p in paths if p.endswith(suffix)), None)
    if not metadata_path:
        raise LookupError("Ce personnage n’a pas encore de guide GIHT publié.")
    base = metadata_path.rsplit("/", 1)[0]
    def read_json(path: str, default):
        try:
            return json.loads(fetch("https://raw.githubusercontent.com/Genshin-Impact-Helper-Team/genshin-builds/main/" + path))
        except Exception:
            return default
    metadata = read_json(metadata_path, {})
    mainstats = read_json(base + "/artifacts-mainstats.json", {})
    substats = read_json(base + "/artifacts-substats.json", {})
    artifacts = read_json(base + "/artifacts-sets.json", {})
    talents = read_json(base + "/talents.json", {})
    build_dirs = sorted({path.rsplit("/", 1)[0] for path in paths if path.startswith(base + "/") and path.endswith("/weapons.json")})
    builds = []
    for build_dir in build_dirs:
        weapons = read_json(build_dir + "/weapons.json", {}).get("weapons", [])
        notes = read_json(build_dir + "/build-notes.json", {})
        sets = read_json(build_dir + "/artifacts-sets.json", {}).get("artifact_sets", []) or artifacts.get("artifact_sets", [])
        main = read_json(build_dir + "/artifacts-mainstats.json", {}).get("main_stats", {}) or mainstats.get("main_stats", {})
        subs = read_json(build_dir + "/artifacts-substats.json", {}).get("substats_priority", []) or substats.get("substats_priority", [])
        builds.append({"role": notes.get("name", {}).get("fr") or notes.get("name", {}).get("en") or build_dir.split("/")[-1], "best": bool(notes.get("best")), "weapons": weapons, "artifacts": sets, "mainStats": main, "substats": subs, "notes": [n.get("fr") or n.get("en", "") for n in notes.get("notes", []) if isinstance(n, dict)], "lastUpdated": notes.get("last_updated", metadata.get("last_updated", ""))})
    builds.sort(key=lambda b: not b["best"])
    return {"character": slug, "source": "Genshin Impact Helper Team · Community Builds", "sourceUrl": "https://github.com/Genshin-Impact-Helper-Team/genshin-builds", "updatedAt": now, "version": metadata.get("last_updated", ""), "roles": metadata.get("roles", []), "talents": talents.get("talents", []), "builds": builds}

def html_text(markup: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", markup))).strip()


def lore_intro(wikitext: str) -> str:
    lead = re.split(r"\n==+", wikitext, maxsplit=1)[0]
    lead = re.sub(r"(?s)<!--.*?-->", " ", lead)
    lead = re.sub(r"(?s)<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", " ", lead, flags=re.I)
    # Strip nested infobox/templates from the lead without leaving fragments.
    for _ in range(8):
        cleaned = re.sub(r"(?s)\{\{[^{}]*\}\}", " ", lead)
        if cleaned == lead:
            break
        lead = cleaned
    def wiki_link(match: re.Match[str]) -> str:
        target, label = match.group(1), match.group(2)
        return (label or target).replace("_", " ").strip()
    lead = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", wiki_link, lead)
    lead = re.sub(r"\[(?:https?://\S+\s+)?([^\]]+)\]", r"\1", lead)
    lead = re.sub(r"'{2,5}", "", lead)
    lead = re.sub(r"<[^>]+>|\[\[.*?\]\]|\{\{.*?\}\}", " ", lead)
    lead = re.sub(r"[\n\r*#|=]+", " ", lead)
    lead = unescape(lead)
    lead = re.sub(r"\b(?:of|in|during|after|before|by|from|the|a|an)\s*[,;.]", ".", lead, flags=re.I)
    return re.sub(r"\s+", " ", lead).strip()


def genshin_lore_index() -> bytes:
    """Build a small, cached browse index from public wiki intros and thumbnails.

    Metadata, a cleaned lead section, and a thumbnail are cached for one day.
    The initial collection is deliberately bounded; artwork is lazy-loaded in UI.
    """
    global gi_lore_index_cache
    now = time.time()
    if gi_lore_index_cache and now - gi_lore_index_cache[0] < LORE_INDEX_TTL:
        return gi_lore_index_cache[1]
    if not gi_lore_index_cache:
        try:
            cached = json.loads(GI_LORE_CACHE_FILE.read_text(encoding="utf-8"))
            cached_at = float(cached.get("cachedAt", 0))
            if cached_at and now - cached_at < LORE_INDEX_TTL:
                payload = json.dumps(cached["payload"], ensure_ascii=False).encode("utf-8")
                gi_lore_index_cache = (cached_at, payload)
                return payload
            if cached.get("payload"):
                gi_lore_index_cache = (cached_at, json.dumps(cached["payload"], ensure_ascii=False).encode("utf-8"))
        except Exception:
            pass
    api = "https://genshin-impact.fandom.com/api.php"
    titles: dict[str, set[str]] = {}
    try:
        def category_pages(category: str) -> tuple[str, list[dict]]:
            collected, continuation = [], {}
            for _ in range(5):
                query = urlencode({"action":"query", "list":"categorymembers", "cmtitle":f"Category:{category}", "cmtype":"page", "cmlimit":"100", "format":"json", **continuation})
                data = json.loads(fetch(f"{api}?{query}"))
                collected.extend(data.get("query", {}).get("categorymembers", []))
                continuation = data.get("continue", {})
                if not continuation:
                    break
            return category, collected
        with ThreadPoolExecutor(max_workers=6) as pool:
            category_results = list(pool.map(category_pages, LORE_INDEX_CATEGORIES))
        for category, pages in category_results:
            for page in pages:
                title = str(page.get("title", "")).strip()
                if title and not title.startswith(("File:", "Category:", "Template:", "Help:")):
                    titles.setdefault(title, set()).add(category)
        rows = []
        all_titles = list(titles)[:360]
        for offset in range(0, len(all_titles), 50):
            batch = all_titles[offset:offset + 50]
            # The current Fandom MediaWiki build no longer supports the classic
            # extracts property; request wikitext and page thumbnails instead.
            query = urlencode({"action":"query", "prop":"revisions|pageimages", "titles":"|".join(batch), "rvprop":"content", "rvslots":"main", "piprop":"thumbnail", "pithumbsize":"720", "format":"json", "origin":"*"})
            data = json.loads(fetch(f"{api}?{query}"))
            for page in data.get("query", {}).get("pages", {}).values():
                title = str(page.get("title", "")).strip()
                revisions = page.get("revisions", [])
                wikitext = revisions[0].get("slots", {}).get("main", {}).get("*", "") if revisions else ""
                # Produce a readable lead from wiki markup, omitting infoboxes,
                # references and nested templates rather than raw source text.
                extract = lore_intro(wikitext)
                if not title or len(extract) < 70:
                    continue
                rows.append({"id":str(page.get("pageid", title)), "title":title, "extract":extract[:1600],
                    "image":page.get("thumbnail", {}).get("source", ""),
                    "categories":sorted(titles.get(title, set())),
                    "url":"https://genshin-impact.fandom.com/wiki/" + quote(title.replace(" ", "_"))})
        rows.sort(key=lambda row: (not any(x in " ".join(row["categories"]).lower() for x in ("lore", "histor", "myth", "book")), row["title"].casefold()))
        payload = json.dumps({"updatedAt":datetime.now(timezone.utc).isoformat(), "source":"Genshin Impact Wiki · catégories publiques", "count":len(rows), "target":200, "articles":rows[:300]}, ensure_ascii=False).encode("utf-8")
        if len(rows) >= 200:
            gi_lore_index_cache = (now, payload)
            try:
                GI_LORE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                GI_LORE_CACHE_FILE.write_text(json.dumps({"cachedAt":now,"payload":json.loads(payload)},ensure_ascii=False),encoding="utf-8")
            except OSError:
                pass
            return payload
        if gi_lore_index_cache:
            return gi_lore_index_cache[1]
        return json.dumps({"updatedAt":datetime.now(timezone.utc).isoformat(), "source":"Genshin Impact Wiki", "count":len(rows), "target":200, "articles":rows[:300], "warning":"La source n’a renvoyé qu’un index partiel; il sera retenté à la prochaine actualisation."}, ensure_ascii=False).encode("utf-8")
    except Exception as exc:
        if gi_lore_index_cache:
            return gi_lore_index_cache[1]
        return json.dumps({"updatedAt":"", "source":"Genshin Impact Wiki", "count":0, "target":200, "articles":[], "error":str(exc)}, ensure_ascii=False).encode("utf-8")


def youtube_video_ids(value: str) -> list[str]:
    text = unescape(value or "")
    pattern = r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?(?:[^#\s]*?&)?v=|embed/|shorts/|live/)|youtu\.be/)([\w-]{11})"
    return list(dict.fromkeys(re.findall(pattern, text, re.I)))


def wuthering_cards(category: str) -> bytes:
    # Encore maintains a versioned live-data index, including beta entries and
    # their official icon URLs. Prefer it for resonators and weapons so new
    # releases appear without waiting for a listing-site scrape.
    if category in {"character", "weapon"}:
        route = "character" if category == "character" else "weapon"
        try:
            payload = json.loads(fetch(f"https://api-v2.encore.moe/api/en/{route}?v=Beta"))
            source_rows = payload.get("roleList" if category == "character" else "weapons", [])
            cards = []
            for row in source_rows:
                name = str(row.get("Name") or "").strip()
                identifier = row.get("Id")
                if not name or identifier is None:
                    continue
                if category == "character":
                    icon = row.get("RoleHeadIconLarge") or row.get("RoleHeadIcon") or row.get("RoleHeadIconBig") or ""
                    element = row.get("Element") or {}
                    weapon_type = row.get("WeaponType") or {}
                    cards.append({
                        "id": re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-"),
                        "apiId": str(identifier), "name": name,
                        "element": element.get("Name", ""),
                        "weaponType": weapon_type.get("Name", ""),
                        "rarity": int(row.get("QualityId") or 5),
                        "imageUrl": icon, "portraitUrl": icon,
                        "sourceUrl": f"https://api-v2.encore.moe/api/en/character/{identifier}?v=Beta",
                        "source": "Encore API · catalogue Beta",
                    })
                else:
                    icon = row.get("Icon") or ""
                    cards.append({
                        "id": str(identifier), "name": name,
                        "weaponType": row.get("TypeName") or "",
                        "rarity": int(row.get("QualityId") or 4),
                        "imageUrl": icon, "iconUrl": icon,
                        "sourceUrl": f"https://api-v2.encore.moe/api/en/weapon/{identifier}?v=Beta",
                        "source": "Encore API · catalogue Beta",
                    })
            if cards:
                return json.dumps(cards, ensure_ascii=False).encode("utf-8")
        except Exception:
            # Keep the maintained WutheringDB listing as a fallback if Encore
            # is temporarily unavailable; cached catalogues remain usable too.
            pass

    route = WW_ROUTES[category]
    html = fetch(f"{BASE}/en/{route}").decode("utf-8", errors="replace")
    pattern = rf'<a\b[^>]*href="/en/{route}/([^"/?#]+)"[^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, flags=re.I | re.S)
    portraits: dict[str, str] = {}
    if category == "character":
        global ww_asset_cache
        now = time.time()
        if not ww_asset_cache or now - ww_asset_cache[0] >= TTL:
            try:
                listing = json.loads(fetch(WW_ASSET_INDEX_URL))
                assets = {re.sub(r"[^a-z0-9]", "", entry.get("name", "").rsplit(".", 1)[0].lower()): entry["download_url"]
                          for entry in listing if entry.get("name", "").lower().endswith(".png") and entry.get("download_url")}
                ww_asset_cache = (now, assets)
            except Exception:
                assets = ww_asset_cache[1] if ww_asset_cache else {}
        else:
            assets = ww_asset_cache[1]
        portraits = assets
    cards = []
    for slug, body in matches:
        title = re.search(r"<h2\b[^>]*>(.*?)</h2>", body, flags=re.I | re.S)
        if not title:
            title = re.search(r"<h[23]\b[^>]*>(.*?)</h[23]>", body, flags=re.I | re.S)
        name = html_text(title.group(1)) if title else slug.replace("-", " ").title()
        paragraphs = [html_text(v) for v in re.findall(r"<p\b[^>]*>(.*?)</p>", body, flags=re.I | re.S)]
        rarity = re.search(r"([45])-Star", body, flags=re.I)
        # Prefer maintained transparent character renders; the listing's old
        # roleportrait URLs have gone stale and return 404s.
        portrait = portraits.get(re.sub(r"[^a-z0-9]", "", name.lower()), "")
        if not portrait and slug == "rover-aero":
            portrait = portraits.get("roveraeromale", "")
        record = {
            "id": slug,
            "name": name,
            "description": paragraphs[-1] if paragraphs else "",
            "subtitle": paragraphs[0] if paragraphs else "",
            "imageUrl": portrait or "",
            "portraitUrl": portrait,
            "rarity": int(rarity.group(1)) if rarity else 5,
            "sourceUrl": f"{BASE}/en/{route}/{slug}",
        }
        cards.append(record)
    return json.dumps(cards, ensure_ascii=False).encode("utf-8")


def genshin_events() -> bytes:
    # Calendar API exposes structured, localized rewards. Keep only active/upcoming
    # in-game activities that actually list Primogems, and include banners separately.
    try:
        payload = json.loads(fetch("https://api.ennead.cc/mihoyo/genshin/calendar?lang=fr-fr"))
        now = int(time.time())
        def iso(stamp: object) -> str:
            try: return datetime.fromtimestamp(int(stamp), timezone.utc).isoformat().replace("+00:00", "Z")
            except (TypeError, ValueError, OverflowError): return ""
        events = []
        for row in payload.get("events", []):
            end = int(row.get("end_time") or 0)
            if not end or end < now: continue
            rewards = list(row.get("rewards") or [])
            special = row.get("special_reward") or {}
            primo_rows = [r for r in [*rewards, special] if "primo" in str(r.get("name", "")).casefold() and int(r.get("amount") or 0) > 0]
            primogems = sum(int(r.get("amount") or 0) for r in primo_rows)
            if not primogems: continue
            title = str(row.get("name") or "Événement Genshin")
            item_kind = "onslaught" if "hardchallenge" in str(row.get("type_name", "")).casefold() else "event"
            events.append({"id": f"ennead:event:{row.get('id', title)}", "kind": item_kind, "title": title,
                "start": iso(row.get("start_time")), "end": iso(row.get("end_time")), "image": row.get("image_url", ""),
                "icons": [], "primogems": primogems, "description": str(row.get("description") or ""),
                "source": {"title": "Calendrier HoYoverse via Ennead API", "url": "https://api.ennead.cc/mihoyo/genshin/calendar?lang=fr-fr"},
                "rewards": [{"name": r.get("name"), "amount": r.get("amount"), "icon": r.get("icon", "")} for r in primo_rows], "type": row.get("type_name", "")})
        for row in payload.get("banners", []):
            end = int(row.get("end_time") or 0)
            if not end or end < now: continue
            kind = "weapon-banner" if row.get("weapons") else "char-banner"
            featured = row.get("weapons") or row.get("characters") or []
            events.append({"id": f"ennead:banner:{row.get('id', row.get('name', ''))}", "kind": kind, "title": str(row.get("name") or "Vœux"),
                "start": iso(row.get("start_time")), "end": iso(row.get("end_time")), "image": "",
                "icons": [{"name": x.get("name", ""), "src": x.get("icon", ""), "rarity": x.get("rarity")} for x in featured], "primogems": None,
                "description": " · ".join(x.get("name", "") for x in featured), "source": {"title": "Calendrier HoYoverse via Ennead API", "url": "https://api.ennead.cc/mihoyo/genshin/calendar?lang=fr-fr"}})
        events.sort(key=lambda x: x.get("start", ""))
        return json.dumps({"updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "Ennead API · calendrier HoYoverse, événements et récompenses", "events": events}, ensure_ascii=False).encode("utf-8")
    except Exception:
        pass
    # GenshinFlex remains a fallback if the structured calendar API is unavailable.
    page = fetch("https://genshinflex.com/en/calendar/").decode("utf-8", errors="replace")
    match = re.search(r'<script[^>]+id="cal-data"[^>]*>(.*?)</script>', page, re.I | re.S)
    if not match: raise ValueError("Le calendrier public ne fournit pas ses données structurées.")
    rows = json.loads(match.group(1))
    events = [{"id": x.get("id"), "kind": x.get("kind"), "title": x.get("title"), "start": x.get("start"), "end": x.get("end"), "image": x.get("image"), "icons": x.get("icons", []), "primogems": x.get("primogems"), "description": x.get("description", ""), "source": x.get("source", {})} for x in rows if x.get("kind") in {"event", "char-banner", "weapon-banner", "version", "theater", "abyss", "onslaught"}]
    return json.dumps({"updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "GenshinFlex calendar · données officielles des annonces", "events": events}, ensure_ascii=False).encode("utf-8")


def _xml_text(node: ET.Element | None) -> str:
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


def _news_timestamp(value: str) -> float:
    """Normalize RFC-822 RSS dates and ISO timestamps before merging feeds."""
    if not value:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _official_news_feed(url: str, category: str, limit: int = 24, payload: bytes | None = None) -> list[dict]:
    root = ET.fromstring(payload if payload is not None else fetch(url))
    rows = []
    for item in root.findall(".//item")[:limit]:
        title = _xml_text(item.find("title"))
        link = _xml_text(item.find("link"))
        description = _xml_text(item.find("description"))
        pub = _xml_text(item.find("pubDate"))
        media = item.find("enclosure")
        image = media.attrib.get("url", "") if media is not None else ""
        if not image:
            encoded = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            match = re.search(r'<img[^>]+src=["\']([^"\']+)', encoded.text or "", re.I) if encoded is not None else None
            image = match.group(1) if match else ""
        hay = f"{category} {title} {description}".lower()
        kind = "special-program" if re.search(r"special program|programme spécial|programme special|preview program", hay) else "event" if re.search(r"event|événement|evenement", hay) else "banner" if re.search(r"banner|bannière|banniere|wish|vœux", hay) else "update" if re.search(r"version|update|mise à jour|mise a jour|maintenance", hay) else "news"
        primos = re.search(r"\b([\d][\d\s,.]*)\s*(?:primogems?|primogemmes?|pierres de la fatalité)\b", description, re.I)
        videos = youtube_video_ids(description)
        rows.append({"id": link or title, "title": title, "description": description[:1200], "link": link, "date": pub, "image": image, "category": kind, "source": "HoYoverse · Genshin Impact", "primogems": int(re.sub(r"\D", "", primos.group(1))) if primos else None, "videos": videos})
    return rows


def _official_hoyoverse_news(payload: bytes) -> list[dict]:
    """Read the same public content API used by the official Genshin news page."""
    data = json.loads(payload)
    rows = []
    for item in data.get("data", {}).get("list", []):
        title = item.get("sTitle", "")
        if not title:
            continue
        info_id = str(item.get("iInfoId", ""))
        content = item.get("sContent", "")
        description = html_text(item.get("sIntro", "") or content)
        searchable = f"{title} {description}".lower()
        category = "special-program" if re.search(r"special program|programme spécial|programme special", searchable) else "event" if re.search(r"event|événement|evenement", searchable) else "banner" if re.search(r"banner|bannière|banniere|vœux", searchable) else "update" if re.search(r"version|mise à jour|mise a jour|maintenance", searchable) else "news"
        try:
            ext = json.loads(item.get("sExt", "{}") or "{}")
        except (TypeError, json.JSONDecodeError):
            ext = {}
        banners = ext.get("banner", [])
        image = next((x.get("url", "") for x in banners if isinstance(x, dict)), "")
        raw_date = item.get("dtCreateTime", "")
        try:
            created = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            date = created.isoformat()
        except (TypeError, ValueError):
            date = raw_date
        plain_content = html_text(content)
        primos = re.search(r"\b([\d][\d\s,.]*)\s*(?:primogems?|primogemmes?|primo-gemmes?|primo-gemmes?|pierres de la fatalité)\b", plain_content, re.I)
        videos = youtube_video_ids(content)
        rows.append({"id": f"hoyoverse:{info_id}", "title": title, "description": description[:1400], "content": plain_content[:24000], "link": item.get("sUrl") or f"https://genshin.hoyoverse.com/fr/news/detail/{info_id}", "date": date, "image": image, "category": category, "source": "HoYoverse · actualité officielle", "feed": "Site officiel", "primogems": int(re.sub(r"\D", "", primos.group(1))) if primos else None, "videos": videos})
    return rows


def genshin_news() -> bytes:
    feeds = [("official", "https://genshin-feed.com/feed/rss-fr-all-articles.xml", "Actualités officielles"), ("feed-events", "https://genshin-feed.com/feed/rss-fr-events.xml", "Événements")]
    youtube_source = "https://www.youtube.com/feeds/videos.xml?channel_id=UCiS882YPwZt1NfaM0gR0D9Q"
    sources = {"official-api": "https://sg-public-api-static.hoyoverse.com/content_v2_user/app/a1b1f9d3315447cc/getContentList?iAppId=32&iChanId=395&iPageSize=40&iPage=1&sLangKey=fr-fr", "hoyolab": "https://bbs-api-os.hoyolab.com/community/post/wapi/getNewsList?gids=2&page_size=30&type=1", **{key: url for key, url, _ in feeds}}
    raw, errors = {}, []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch, url): key for key, url in sources.items()}
        for future, key in futures.items():
            try: raw[key] = future.result(timeout=22)
            except Exception as exc: errors.append(f"{key}: {exc}")
    articles: dict[str, dict] = {}
    try:
        for row in _official_hoyoverse_news(raw["official-api"]):
            articles[row["id"]] = row
    except Exception as exc:
        errors.append(f"Site officiel Genshin: {exc}")
    for key, url, label in feeds:
        try:
            for row in _official_news_feed(url, label, payload=raw.get(key)):
                row["feed"] = label
                articles[row["id"]] = row
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    # HoYoLAB's public, read-only announcement endpoint. No account token is used.
    try:
        data = json.loads(raw["hoyolab"])
        for entry in data.get("data", {}).get("list", []):
            post = entry.get("post", {})
            title = post.get("subject", "")
            post_id = str(post.get("post_id", ""))
            if not title or not post_id:
                continue
            text = re.sub(r"<[^>]+>", " ", post.get("content", ""))
            images = post.get("images", [])
            cover = post.get("cover", "")
            created = int(post.get("created_at", 0) or 0)
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created)) if created else ""
            hay = f"{title} {text}".lower()
            kind = "special-program" if re.search(r"special program|programme spécial|programme special", hay) else "event" if re.search(r"event|événement|evenement", hay) else "banner" if re.search(r"banner|bannière|banniere|vœux", hay) else "update" if re.search(r"version|update|mise à jour|mise a jour", hay) else "news"
            primos = re.search(r"\b([\d][\d\s,.]*)\s*(?:primogems?|primogemmes?|pierres de la fatalité)\b", text, re.I)
            articles[f"hoyolab:{post_id}"] = {"id": f"hoyolab:{post_id}", "title": title, "description": text[:1200], "link": f"https://www.hoyolab.com/article/{post_id}", "date": stamp, "image": cover or (images[0].get("url", "") if images and isinstance(images[0], dict) else ""), "category": kind, "source": "HoYoLAB · annonce officielle", "feed": "HoYoLAB", "primogems": int(re.sub(r"\D", "", primos.group(1))) if primos else None, "videos": []}
    except Exception as exc:
        errors.append(f"HoYoLAB: {exc}")
    # Official YouTube uploads are exposed as Atom. The feed can fail temporarily,
    # so retry it and retain videos linked from official articles as a fallback.
    videos = []
    youtube_error = None
    for attempt in range(3):
        try:
            atom = ET.fromstring(fetch(youtube_source))
            ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
            for entry in atom.findall("a:entry", ns)[:12]:
                video_id = _xml_text(entry.find("yt:videoId", ns))
                title = _xml_text(entry.find("a:title", ns))
                if not video_id or not title: continue
                videos.append({"id": video_id, "title": title, "date": _xml_text(entry.find("a:published", ns)), "link": f"https://www.youtube.com/watch?v={video_id}", "embed": f"https://www.youtube-nocookie.com/embed/{video_id}", "image": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg", "source": "YouTube · Genshin Impact officiel"})
            youtube_error = None
            break
        except Exception as exc:
            youtube_error = exc
            if attempt < 2: time.sleep(0.6 * (attempt + 1))
    known_video_ids = {video["id"] for video in videos}
    for article in sorted(articles.values(), key=lambda row: _news_timestamp(row.get("date", "")), reverse=True):
        for video_id in article.get("videos", []):
            if video_id in known_video_ids: continue
            known_video_ids.add(video_id)
            videos.append({"id": video_id, "title": article.get("title", "Vidéo liée à une annonce Genshin"), "date": article.get("date", ""), "link": f"https://www.youtube.com/watch?v={video_id}", "embed": f"https://www.youtube-nocookie.com/embed/{video_id}", "image": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg", "source": "Vidéo · annonce Genshin officielle"})
    if youtube_error and not videos: errors.append(f"YouTube temporairement indisponible: {youtube_error}")
    ordered = sorted(articles.values(), key=lambda row: _news_timestamp(row.get("date", "")), reverse=True)
    return json.dumps({"updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "HoYoverse / HoYoLAB / YouTube", "articles": ordered[:60], "videos": videos, "errors": errors}, ensure_ascii=False).encode("utf-8")


def genshin_tierlist_status() -> bytes:
    # Reader endpoint supplies page metadata when Prydwen blocks server-side requests.
    text = fetch("https://r.jina.ai/https://www.prydwen.gg/genshin-impact/tier-list").decode("utf-8", errors="replace")
    published = re.search(r"Published Time:\s*([^\r\n]+)", text)
    updated = re.search(r"Last updated:\*\*\s*([^*\r\n]+)", text, re.I)
    version = re.search(r"Genshin Impact Tier List \(([^)]+)\)", text)
    changelog = re.search(r"(?im)^Changelog\s*$", text)
    return json.dumps({"checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "publishedAt": published.group(1).strip() if published else "", "lastUpdated": updated.group(1).strip() if updated else "", "version": version.group(1) if version else "", "source": "Prydwen", "page": "https://www.prydwen.gg/genshin-impact/tier-list", "changelogAvailable": bool(changelog)}, ensure_ascii=False).encode("utf-8")


_THEATER_DB_ICON_CACHE: dict[str, str] = {}
def theater_db_icon(name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
    if key in _THEATER_DB_ICON_CACHE: return _THEATER_DB_ICON_CACHE[key]
    icon = ""
    try:
        url = "https://genshin-db-api.vercel.app/api/v5/enemies?" + urlencode({"query": name, "matchCategories": "true", "verboseCategories": "true", "resultLanguage": "English"})
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Astralis/1.0)", "Accept": "application/json"})
        with urlopen(request, timeout=6) as response: row = json.loads(response.read())
        candidates = row if isinstance(row, list) else [row]
        wanted = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
        for candidate in candidates:
            found = re.sub(r"[^a-z0-9]+", " ", str(candidate.get("name", "")).casefold()).strip()
            if found == wanted or (len(wanted) > 12 and (wanted in found or found in wanted)):
                filename = (candidate.get("images") or {}).get("filename_icon", "")
                if filename: icon = "https://gi.yatta.moe/assets/UI/monster/" + quote(filename, safe="") + ".png"
                break
    except Exception: pass
    if not icon and "samachurl" in key:
        icon = "https://gi.yatta.moe/assets/UI/monster/UI_MonsterIcon_Shaman_Rock_01.png"
    _THEATER_DB_ICON_CACHE[key] = icon
    return icon

def current_theater_from_public_guide() -> dict | None:
    """Fallback for the monthly Theater roster when GenshinFlex has not rolled over yet."""
    page = fetch("https://insider-gaming.com/genshin-impact-imaginarium-theater/").decode("utf-8", "replace")
    month = datetime.now().strftime("%B")
    year = datetime.now().year
    title = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.I | re.S)
    title_text = html_text(title.group(1)) if title else ""
    if month.casefold() not in title_text.casefold() or str(year) not in title_text:
        return None
    details = re.search(r"available elements for the Imaginarium Theater .*? are ([^.]+)", html_text(page), re.I)
    split_names = lambda value: [x.strip() for x in re.split(r"\s*,\s*|\s+and\s+", value.replace(", and ", ", ")) if x.strip()]
    elements = split_names(details.group(1)) if details else []
    cast_match = re.search(r"Opening Characters include ([^.]+)", html_text(page), re.I)
    opening = split_names(cast_match.group(1)) if cast_match else []
    guest_match = re.search(r"Special Guest Stars include ([^.]+)", html_text(page), re.I)
    guests = split_names(guest_match.group(1)) if guest_match else []
    bosses = []
    for heading in re.findall(r"<h2[^>]*>(.*?)</h2>", page, re.I | re.S):
        text = html_text(heading)
        match = re.match(r"Act\s+(\d+)\s*[—–-]\s*(.+)", text, re.I)
        if match:
            name = match.group(2).strip()
            bosses.append({"name": f"Acte {match.group(1)}", "enemies": [{"name": name, "icon": theater_db_icon(name)}]})
    if not elements:
        return None
    today = datetime.now()
    start = today.replace(day=1, hour=4, minute=0, second=0, microsecond=0)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1, hour=4, minute=0, second=0, microsecond=0)
    return {"title": title_text, "period": f"1 {month} — 1 {end.strftime('%B')}", "elements": elements,
            "opening": opening, "guests": guests, "bosses": bosses,
            "source": "Insider Gaming · guide de rotation mensuelle"}


def genshin_endgame() -> bytes:
    abyss = fetch(ENDGAME_URLS[0]).decode("utf-8", errors="replace")
    theater = fetch(ENDGAME_URLS[1]).decode("utf-8", errors="replace")
    onslaught = fetch(ENDGAME_URLS[2]).decode("utf-8", errors="replace")
    blessing_match = re.search(r'<div class="panel blessing"[^>]*>.*?<p[^>]*>(.*?)</p>', abyss, re.I | re.S)
    floors = []
    sections = list(re.finditer(r'<section id="floor-(\d+)" class="floor"[^>]*>(.*?)(?=<section id="floor-\d+" class="floor"|</main>)', abyss, re.I | re.S))
    for section in sections:
        floor_no, body = section.groups()
        level = re.search(r'enemy levels?\s*([^<]+)', body, re.I)
        disorder_list = re.search(r'<ul class="disorder"[^>]*>(.*?)</ul>', body, re.I | re.S)
        disorder = [html_text(v).replace("Disorder", "Bonus de trouble") for v in re.findall(r'<li\b[^>]*>(.*?)</li>', disorder_list.group(1), re.I | re.S)] if disorder_list else []
        chambers = []
        for chamber in re.findall(r'<article class="panel chamber"[^>]*>(.*?)</article>', body, re.I | re.S):
            heading = re.search(r'<h3[^>]*>(.*?)</h3>', chamber, re.I | re.S)
            halves = []
            for half in re.findall(r'<div class="half"[^>]*>(.*?)(?=<div class="half"|$)', chamber, re.I | re.S):
                label = re.search(r'<span class="hl"[^>]*>(.*?)</span>', half, re.I | re.S)
                enemies = []
                for enemy in re.findall(r'<li class="enemy"[^>]*>(.*?)</li>', half, re.I | re.S):
                    icon = re.search(r'<img[^>]+src="([^"]+)"', enemy, re.I)
                    name = re.search(r'<span[^>]*>(.*?)</span>', enemy, re.I | re.S)
                    if name:
                        enemies.append({"name": html_text(name.group(1)), "icon": urljoin("https://genshinflex.com/", unescape(icon.group(1))) if icon else ""})
                note_match = re.search(r'<p class="muted small"[^>]*>(.*?)</p>', half, re.I | re.S)
                halves.append({"name": html_text(label.group(1)).replace("Half 1", "1re moitié").replace("Half 2", "2e moitié") if label else "Moitié", "enemies": enemies, "note": html_text(note_match.group(1)) if note_match else ""})
            if heading:
                chambers.append({"name": html_text(heading.group(1)).replace("Chamber", "Salle"), "halves": halves})
        floors.append({"floor": floor_no, "levels": html_text(level.group(1)) if level else "", "disorder": " · ".join(disorder), "chambers": chambers})
    cycle = re.search(r'<article class="panel cycle"[^>]*data-history-item[^>]*>(.*?)(?=<article class="panel cycle"|</main>)', theater, re.I | re.S)
    cycle_html = cycle.group(1) if cycle else ""
    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', cycle_html, re.I | re.S)
    period_match = re.search(r'<p class="muted small"[^>]*>(.*?)</p>', cycle_html, re.I | re.S)
    groups = {}
    for group in re.finditer(r'<div class="cast-group"[^>]*>\s*<h4[^>]*>(.*?)</h4>(.*?)(?=<div class="cast-group"|$)', cycle_html, re.I | re.S):
        names = re.findall(r'<a class="ci"[^>]*title="([^"]+)"', group.group(2), re.I)
        groups[html_text(group.group(1)).lower()] = [html_text(x) for x in names]
    elements = re.search(r'data-elements="([^"]*)"', cycle.group(0), re.I) if cycle else None
    def french_months(text: str) -> str:
        months = {"January":"janvier", "February":"février", "March":"mars", "April":"avril", "May":"mai", "June":"juin", "July":"juillet", "August":"août", "September":"septembre", "October":"octobre", "November":"novembre", "December":"décembre"}
        text = re.sub(r"\b([A-Za-z]+)\s+(\d+)\b", lambda m: f"{m.group(2)} {months.get(m.group(1), m.group(1))}" if m.group(1) in months else m.group(0), text)
        for english, french in months.items():
            text = re.sub(rf"\b{english}\b", french, text, flags=re.I)
        return text.replace("Anemo", "Anémo").replace("Season", "Saison").replace("Imaginarium Theater", "Théâtre de l’imaginarium").replace("elements:", "éléments :")
    element_names = {"hydro":"Hydro", "cryo":"Cryo", "anemo":"Anémo", "pyro":"Pyro", "electro":"Électro", "dendro":"Dendro", "geo":"Géo"}
    theater_bosses = []
    # GenshinFlex keeps boss portraits in the season's enemy-list markup. Index
    # these URLs before parsing the compact "Main villains" text summary.
    theater_enemy_icons = {}
    for enemy_html in re.findall(r'<li class="enemy"[^>]*>(.*?)</li>', theater, re.I | re.S):
        enemy_name = re.search(r'<span[^>]*>(.*?)</span>', enemy_html, re.I | re.S)
        enemy_image = re.search(r'<img[^>]+src="([^"]+)"', enemy_html, re.I)
        if enemy_name and enemy_image:
            clean_name = re.sub(r'\s*<small.*$', '', enemy_name.group(1), flags=re.I | re.S)
            theater_enemy_icons[html_text(clean_name).lower()] = urljoin("https://genshinflex.com/", unescape(enemy_image.group(1)))
    villain_line = re.search(r'Main villains:\s*(.*?)</li>', cycle_html, re.I | re.S)
    if villain_line:
        villain_text = html_text(villain_line.group(1))
        for chunk in re.split(r',\s*(?=Act\s+\d+)', villain_text):
            match = re.match(r'Act\s+(\d+)\s*[—–:-]?\s*(.*)', chunk, re.I)
            if not match: continue
            stage, names = match.groups()
            candidates = re.split(r'\s+or\s+', names, flags=re.I)
            enemies = []
            for name in candidates:
                clean = re.sub(r'\s*\([^)]*mode[^)]*\)', '', name, flags=re.I).strip()
                clean = re.sub(r'\s*·\s*enhanced version', '', clean, flags=re.I).strip()
                icon = theater_enemy_icons.get(clean.lower(), '')
                if not icon:
                    icon = next((url for known, url in theater_enemy_icons.items() if clean.lower() in known or known in clean.lower()), '')
                if not icon: icon = theater_db_icon(re.sub(r"\s*\([^)]*\)", "", clean).strip())
                if clean: enemies.append({"name": clean, "icon": icon})
            theater_bosses.append({"name": f"Acte {stage}", "enemies": enemies})
    for boss in re.findall(r'<div class="boss"[^>]*>(.*?)</div>', cycle_html, re.I | re.S):
        heading = re.search(r'<h4[^>]*>(.*?)</h4>', boss, re.I | re.S)
        enemies = []
        for enemy in re.findall(r'<li class="enemy"[^>]*>(.*?)</li>', boss, re.I | re.S):
            icon = re.search(r'<img[^>]+src="([^"]+)"', enemy, re.I)
            name = re.search(r'<span[^>]*>(.*?)</span>', enemy, re.I | re.S)
            if name:
                enemies.append({"name": html_text(name.group(1)), "icon": urljoin("https://genshinflex.com/", unescape(icon.group(1))) if icon else ""})
        if enemies and (not heading or "main villains" not in html_text(heading.group(1)).lower()): theater_bosses.append({"name": html_text(heading.group(1)) if heading else "Boss", "enemies": enemies})
    blessing_text = html_text(blessing_match.group(1)) if blessing_match else ""
    for english, french in (("Abyssal Moon blessing:", "Bénédiction de la lune abyssale :"), ("Disorder", "Bonus de trouble"), ("Superconduct", "Supraconduction"), ("Frozen", "Gel"), ("Shatter", "Brisé"), ("Time left over", "Temps restant")):
        blessing_text = blessing_text.replace(english, french)
    on_title_match = re.search(r'<h1[^>]*>.*?</h1>\s*<p class="muted"[^>]*>(.*?)</p>', onslaught, re.I | re.S)
    on_period_match = re.search(r'<b[^>]+data-until="([^"]+)"', onslaught, re.I)
    on_date_match = re.search(r'<span class="muted small"[^>]*>([A-Za-z]+\s+\d+\s*[—-]+\s*[A-Za-z]+\s+\d+)</span>', onslaught, re.I)
    on_elements = []
    intro = re.search(r'<div class="row"[^>]*>(.*?)(?=<div class="panel when"|</header>)', onslaught, re.I | re.S)
    if intro:
        on_elements = [html_text(x) for x in re.findall(r'<span class="chip gold"[^>]*>(.*?)</span>', intro.group(1), re.I | re.S)]
    on_bosses = []
    stage_sections = list(re.finditer(r'<article id="stage-(\d+)" class="panel stage"[^>]*>(.*?)(?=<article id="stage-\d+" class="panel stage"|</div>\s*</section>)', onslaught, re.I | re.S))
    if not stage_sections:
        stage_sections = list(re.finditer(r'<article id="stage-(\d+)" class="panel stage"[^>]*>(.*?)(?=<article id="stage-\d+" class="panel stage"|<section class="videos")', onslaught, re.I | re.S))
    for stage in stage_sections:
        stage_no, body = stage.groups()
        stage_title = re.search(r'<span class="chip"[^>]*>(.*?)</span>', body, re.I | re.S)
        boss_group = re.search(r'<span class="hl"[^>]*>Boss</span>\s*<ul[^>]*>(.*?)</ul>', body, re.I | re.S)
        enemies = []
        if boss_group:
            for enemy in re.findall(r'<li class="enemy"[^>]*>(.*?)</li>', boss_group.group(1), re.I | re.S):
                icon = re.search(r'<img[^>]+src="([^"]+)"', enemy, re.I)
                name = re.search(r'<span[^>]*>(.*?)</span>', enemy, re.I | re.S)
                if name:
                    enemies.append({"name": html_text(name.group(1)), "icon": urljoin("https://genshinflex.com/", unescape(icon.group(1))) if icon else ""})
        weak = re.search(r'<div class="weak"[^>]*>(.*?)</div>', body, re.I | re.S)
        advantages = [html_text(x) for x in re.findall(r'<span class="chip gold"[^>]*>(.*?)</span>', weak.group(1), re.I | re.S)] if weak else []
        on_bosses.append({"stage": stage_no, "name": html_text(stage_title.group(1)) if stage_title else f"Combat {stage_no}", "enemies": enemies, "advantages": advantages})
    onslaught_data = {"title": (re.search(r"Version\s+([\d.]+)", html_text(on_title_match.group(1)), re.I) and f"Version {re.search(r'Version\s+([\d.]+)', html_text(on_title_match.group(1)), re.I).group(1)} · rotation actuelle") if on_title_match else "Carnage chtonien", "period": french_months(html_text(on_date_match.group(1))) if on_date_match else "", "endAt": on_period_match.group(1) if on_period_match else "", "elements": on_elements, "bosses": on_bosses}
    theater_data = {"title": french_months(html_text(title_match.group(1))) if title_match else "Théâtre de l’imaginarium",
                    "period": french_months(html_text(period_match.group(1))) if period_match else "",
                    "elements": [element_names.get(x.lower(), x) for x in (elements.group(1).split() if elements else [])],
                    "opening": next((v for k,v in groups.items() if "opening" in k), []),
                    "guests": next((v for k,v in groups.items() if "special guest" in k), []), "bosses": theater_bosses,
                    "source": "GenshinFlex"}
    try:
        live_theater = current_theater_from_public_guide()
        if live_theater:
            theater_data = live_theater
    except Exception:
        pass
    result = {"updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "blessing": blessing_text,
              "floors": floors,
              "theater": theater_data,
              "onslaught": onslaught_data}
    return json.dumps(result, ensure_ascii=False).encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print("[Astralis] " + (fmt % args))

    def _host_auth_ok(self) -> bool:
        password = os.environ.get("ASTRALIS_PASSWORD", "")
        if not (os.environ.get("RENDER") or password): return True
        if os.environ.get("RENDER") and len(password) < 16:
            self.send_response(503)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        expected = "Basic " + __import__("base64").b64encode(("astralis:" + password).encode()).decode()
        if secrets.compare_digest(self.headers.get("Authorization", ""), expected): return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Astralis", charset="UTF-8"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_POST(self) -> None:
        global _HOYOLAB_RESIN_CACHE
        if not self._host_auth_ok(): return
        path = urlsplit(self.path).path
        if path not in {"/api/hoyolab/credentials", "/api/hoyolab/disconnect"}:
            self.send_json(404, {"error":"Route inconnue."}); return
        origin = self.headers.get("Origin", "")
        allowed_origins = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
        if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
            allowed_origins.add("https://" + os.environ["RENDER_EXTERNAL_HOSTNAME"])
        if origin and origin not in allowed_origins:
            self.send_json(403, {"error":"Origine refusée."}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 8192: raise ValueError("Taille de requête invalide.")
            body = json.loads(self.rfile.read(length))
            if path.endswith("/disconnect"):
                _write_hoyolab_secret(None)
                _HOYOLAB_RESIN_CACHE = None
                self.send_json(200, {"ok":True}); return
            uid = str(body.get("uid", "")).strip()
            region = str(body.get("region", "os_euro"))
            cookie = str(body.get("cookie", "")).strip()
            if not re.fullmatch(r"\d{8,12}", uid): raise ValueError("Saisis un UID Genshin valide (8 à 12 chiffres).")
            if region not in {"os_usa", "os_euro", "os_asia", "os_cht"}: raise ValueError("Serveur Genshin invalide.")
            if not cookie or len(cookie) > 6000 or "=" not in cookie or "\r" in cookie or "\n" in cookie: raise ValueError("Colle uniquement les cookies de session HoYoLAB valides.")
            _write_hoyolab_secret({"uid":uid,"region":region,"cookie":cookie})
            _HOYOLAB_RESIN_CACHE = None
            storage = "Windows DPAPI · profil utilisateur local" if os.name == "nt" else "Mémoire du serveur · session hébergée"
            self.send_json(200, {"ok":True,"encrypted":os.name == "nt","storage":storage})
        except Exception as exc:
            self.send_json(400, {"error":str(exc)})

    def do_GET(self) -> None:
        request_url = urlsplit(self.path)
        path = request_url.path
        if path != "/health" and not self._host_auth_ok(): return
        refresh = parse_qs(request_url.query).get("refresh") == ["1"]
        if path == "/api/hoyolab/status":
            try:
                auth = _read_hoyolab_secret()
                storage = "Windows DPAPI · profil utilisateur local" if os.name == "nt" else "Mémoire du serveur · session hébergée"
                self.send_json(200, {"connected":bool(auth),"uid":auth.get("uid") if auth else "","storage":storage}); return
            except Exception as exc:
                self.send_json(500, {"connected":False,"error":str(exc)}); return
        if path == "/api/hoyolab/resin":
            try:
                if refresh:
                    global _HOYOLAB_RESIN_CACHE
                    _HOYOLAB_RESIN_CACHE = None
                self.send_json(200, _fetch_hoyolab_resin())
            except LookupError as exc: self.send_json(401, {"error":str(exc)})
            except Exception as exc: self.send_json(502, {"error":str(exc) or "HoYoLAB est momentanément indisponible."})
            return
        if path == "/health":
            self.send_json(200, {"ok": True, "message": "Astralis local data bridge active"})
            return
        if path == "/api/gi/aiynao":
            key = "gi/aiynao"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                payload = entry[1] if entry and now - entry[0] < 1800 else None
                stale_payload = entry[1] if entry else None
            if payload is None:
                try:
                    videos = []
                    try:
                        feed = ET.fromstring(fetch("https://www.youtube.com/feeds/videos.xml?channel_id=UCBaB1WEGbMC4XmEh_cXxjlA"))
                        atom = "{http://www.w3.org/2005/Atom}"; yt = "{http://www.youtube.com/xml/schemas/2015}"
                        for item in feed.findall(atom + "entry"):
                            video_id=(item.findtext(yt + "videoId") or "").strip(); title=(item.findtext(atom + "title") or "").strip(); published=(item.findtext(atom + "published") or "")[:10]
                            if video_id and title: videos.append({"id":video_id,"title":title,"published":published})
                    except Exception:
                        # YouTube's public RSS can temporarily return errors; the public channel page is a second read-only source.
                        page=fetch("https://www.youtube.com/@Aiynao/videos").decode("utf-8",errors="replace")
                        seen=set()
                        for match in re.finditer(r'"videoRenderer"\s*:\s*\{(.*?)(?=,"trackingParams"|}},"continuationItemRenderer")',page,re.S):
                            block=match.group(1); ident=re.search(r'"videoId"\s*:\s*"([\w-]{11})"',block); title=re.search(r'"title"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"((?:\\.|[^"])*)"',block)
                            if ident and title and ident.group(1) not in seen:
                                seen.add(ident.group(1)); videos.append({"id":ident.group(1),"title":json.loads('"'+title.group(1)+'"'),"published":""})
                    if not videos: raise RuntimeError("Aucune vidéo récente lisible sur les sources publiques.")
                    payload=json.dumps({"videos":videos[:12],"updatedAt":datetime.now(timezone.utc).isoformat(),"source":"Flux public YouTube · Aiynao"},ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key]=(now,payload)
                except Exception as exc:
                    if stale_payload:
                        stale=json.loads(stale_payload);stale["stale"]=True;stale["warning"]="Flux YouTube indisponible; affichage de la dernière copie conservée.";payload=json.dumps(stale,ensure_ascii=False).encode("utf-8")
                    else:
                        self.send_json(200,{"videos":[],"updatedAt":"","source":"Aiynao","warning":"Flux public momentanément indisponible.","detail":str(exc)})
                        return
            self.send_bytes(200,payload,"application/json; charset=utf-8")
            return
        if path == "/api/gi/lore-index":
            payload = genshin_lore_index()
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/gi/lore":
            title = parse_qs(request_url.query).get("title", [""])[0].strip()
            if not title or len(title) > 100 or not re.fullmatch(r"[\wÀ-ÿ’'(),. -]+", title, re.UNICODE):
                self.send_json(400, {"error": "Titre de lore invalide."}); return
            key = "gi/lore/" + title.casefold()
            now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 43200 else None
            if payload is None:
                try:
                    api = "https://genshin-impact.fandom.com/api.php?action=parse&format=json&prop=text&page=" + quote(title)
                    response = json.loads(fetch(api))
                    page = response.get("parse", {})
                    markup = page.get("text", {}).get("*", "")
                    if markup:
                        markup = re.sub(r'<div[^>]+class="[^"]*(?:custom-tabs|mw-references-wrap|toc)[^"]*"[^>]*>.*?</div>', " ", markup, flags=re.I | re.S)
                        markup = re.sub(r"<(aside|table|figure|nav|script|style)\b[^>]*>.*?</\1>", " ", markup, flags=re.I | re.S)
                        markup = re.sub(r'<span class="mw-editsection"[^>]*>.*?</span>', " ", markup, flags=re.I | re.S)
                        markup = re.sub(r"<h([2-6])\b[^>]*>(.*?)</h\1>", lambda m: "\n\n" + "#" * (int(m.group(1))-1) + " " + html_text(m.group(2)) + "\n", markup, flags=re.I | re.S)
                        markup = re.sub(r"</(p|li|blockquote|section|div)>", "\n", markup, flags=re.I)
                        extract = re.sub(r"\n{3,}", "\n\n", unescape(re.sub(r"<[^>]+>", " ", markup))).strip()
                    else:
                        extract = ""
                    if not extract: raise ValueError("Aucun article correspondant dans le wiki.")
                    payload = json.dumps({"title": page.get("title", title), "extract": extract[:180000], "source": "Genshin Impact Wiki · Fandom", "url": "https://genshin-impact.fandom.com/wiki/" + quote(page.get("title", title).replace(" ", "_"))}, ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La notice communautaire est temporairement indisponible.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/build-reverse":
            query = parse_qs(request_url.query)
            name = (query.get("name", [""])[0] or "").strip()
            kind = query.get("kind", ["artifact"])[0]
            if not name or len(name) > 100 or kind not in {"weapon", "artifact"}:
                self.send_json(400, {"error": "Objet de build invalide."}); return
            key = "gi/build-reverse/" + kind + "/" + name.casefold()
            now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 21600 and not refresh else None
            if payload is None:
                try:
                    aliases = {re.sub(r"[^a-z0-9]+", "", value.casefold()) for value in gi_name_aliases("weapon" if kind == "weapon" else "artifact", name)}
                    rows = gi_build_reverse_index()
                    matches = [row for row in rows if any(re.sub(r"[^a-z0-9]+", "", str(candidate).casefold()) in aliases for candidate in ([row.get("weapon", "")] if kind == "weapon" else row.get("sets", [])))]
                    unique = {}
                    for row in matches: unique.setdefault(re.sub(r"[^a-z0-9]+", "", row.get("name", "").casefold()), row)
                    matches = list(unique.values())[:5]
                    result = {"item": name, "kind": kind, "source": "Genshin.gg · guides de build des personnages", "sourceUrl": "https://genshin.gg/builds/", "updatedAt": now, "characters": matches}
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "L’index de recommandations est temporairement indisponible.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/team-recommendations":
            name = (parse_qs(request_url.query).get("name", [""])[0] or "").strip()
            if not name or len(name) > 80:
                self.send_json(400, {"error": "Nom de personnage invalide."}); return
            key = "gi/team-recommendations/" + name.casefold()
            now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 21600 and not refresh else None
            if payload is None:
                try:
                    aliases = gi_name_aliases("character", name)
                    teams = []
                    for alias in aliases:
                        teams.extend(gi_team_recommendations(alias))
                    unique = {team.get("name"): team for team in teams if team.get("name")}
                    result = {"character": name, "source": "Genshin.gg · équipes populaires et hors méta", "sourceUrl": "https://genshin.gg/teams/", "updatedAt": now, "teams": list(unique.values())[:8]}
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "Les compositions Genshin.gg sont temporairement indisponibles.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/build-guide":
            slug = (parse_qs(request_url.query).get("name", [""])[0] or "").strip()
            key = "gi/build-guide/" + slug.casefold()
            now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 86400 and not refresh else None
            if payload is None:
                try:
                    guide = gi_build_guide(slug)
                    payload = json.dumps(guide, ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key] = (now, payload)
                except LookupError as exc:
                    self.send_json(404, {"error": str(exc)}); return
                except Exception as exc:
                    self.send_json(502, {"error": "Les recommandations GIHT sont temporairement indisponibles.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/character-media":
            name = (parse_qs(request_url.query).get("name", [""])[0] or "").strip()
            if not name or len(name) > 64 or not re.fullmatch(r"[\w .’'()-]+", name, flags=re.UNICODE):
                self.send_json(400, {"error": "Nom de personnage invalide."}); return
            key = "gi/character-media/" + name.casefold()
            now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 86400 else None
            if payload is None:
                try:
                    query = quote(f'"Paimon\'s Paintings" {name}')
                    endpoint = f"https://genshin-impact.fandom.com/api.php?action=query&list=search&srsearch={query}&srnamespace=6&srlimit=12&format=json"
                    results = json.loads(fetch(endpoint)).get("query", {}).get("search", [])
                    pages = [row for row in results if re.search(r"Icon Emoji Paimon.*Paintings", row.get("title", ""), re.I) and name.casefold() in row.get("title", "").casefold()]
                    if pages:
                        titles = "|".join(row["title"] for row in pages[:8])
                        info_url = "https://genshin-impact.fandom.com/api.php?" + urlencode({"action":"query","titles":titles,"prop":"imageinfo","iiprop":"url","iiurlwidth":"220","format":"json"})
                        info = json.loads(fetch(info_url)).get("query", {}).get("pages", {}).values()
                        stickers = [{"title": page.get("title", "").replace("File:", ""), "url": page.get("imageinfo", [{}])[0].get("thumburl") or page.get("imageinfo", [{}])[0].get("url", "")} for page in info if page.get("imageinfo") and (page.get("imageinfo", [{}])[0].get("thumburl") or page.get("imageinfo", [{}])[0].get("url"))]
                    else: stickers = []
                    # Keep a small, optimized-by-source local sticker pack so every page
                    # can reuse the same handful of PNGs without repeatedly contacting the wiki.
                    sticker_dir = Path(__file__).resolve().parent / "assets" / "cache" / "character-emojis"
                    sticker_dir.mkdir(parents=True, exist_ok=True)
                    slug = re.sub(r"[^a-z0-9-]+", "-", name.casefold()).strip("-")[:48] or "character"
                    for index, sticker in enumerate(stickers[:8]):
                        if not sticker.get("url"): continue
                        try:
                            req = Request(sticker["url"], headers={
                                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
                                "Referer":"https://genshin-impact.fandom.com/",
                                "Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                            })
                            with urlopen(req, timeout=8) as response:
                                mime = response.headers.get_content_type(); image_bytes = response.read(512 * 1024 + 1)
                            if len(image_bytes) > 512 * 1024: continue
                            if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"): ext="png"
                            elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP": ext="webp"
                            elif image_bytes.startswith(b"\xff\xd8\xff"): ext="jpg"
                            else: continue
                            target = sticker_dir / f"{slug}-{index + 1}.{ext}"
                            if not target.exists(): target.write_bytes(image_bytes)
                            sticker["url"] = f"/assets/cache/character-emojis/{target.name}"
                        except Exception: pass
                    payload = json.dumps({"character":name,"stickers":stickers,"source":"Genshin Impact Wiki · Emojis Paimon's Paintings","sourceUrl":"https://genshin-impact.fandom.com/wiki/Category:Paimon%27s_Paintings"}, ensure_ascii=False).encode("utf-8")
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error":"Les stickers communautaires ne sont pas disponibles pour le moment.","detail":str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/lore-image":
            title = (parse_qs(request_url.query).get("title", [""])[0] or "").strip()
            if not title or len(title) > 80 or not re.fullmatch(r"[\w À-ÿ’'()-]+", title, flags=re.UNICODE):
                self.send_json(400, {"error":"Titre d’image invalide."}); return
            key = "gi/lore-image/" + title.casefold(); now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 86400 else None
            mime = "image/jpeg"
            if payload is None:
                try:
                    endpoint = "https://genshin-impact.fandom.com/api.php?" + urlencode({"action":"query","titles":title,"prop":"pageimages","piprop":"thumbnail","pithumbsize":"960","format":"json"})
                    pages = json.loads(fetch(endpoint)).get("query",{}).get("pages",{}).values()
                    image_url = next((p.get("thumbnail",{}).get("source") for p in pages if p.get("thumbnail",{}).get("source")), "")
                    if not image_url: raise ValueError("Aucune illustration de personnage référencée par la source.")
                    req = Request(image_url, headers={"User-Agent":"Mozilla/5.0 (compatible; Astralis/1.0)"})
                    with urlopen(req, timeout=12) as response:
                        mime = response.headers.get_content_type(); payload = response.read(5 * 1024 * 1024 + 1)
                    if not mime.startswith("image/") or len(payload) > 5 * 1024 * 1024: raise ValueError("Illustration trop volumineuse ou format invalide.")
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502,{"error":"Illustration Lore momentanément indisponible.","detail":str(exc)}); return
            self.send_bytes(200,payload,mime); return
        if path == "/api/image":
            raw = parse_qs(request_url.query).get("url", [""])[0]
            try:
                target = urlparse(raw)
                allowed = {"enka.network", "gi.yatta.moe", "genshin.jmp.blue", "api.ambr.top", "vizualabstract.github.io", "raw.githubusercontent.com", "upload-os-bbs.hoyolab.com", "act-webstatic.hoyoverse.com", "genshin.hoyoverse.com"}
                if target.scheme != "https" or not any(target.hostname == host or (target.hostname or "").endswith("." + host) for host in allowed):
                    self.send_json(400, {"error": "Source d’image non autorisée."}); return
                key = "image/" + raw
                now = time.time()
                with cache_lock:
                    entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 86400 else None
                mime = "image/png"
                if payload is None:
                    request = Request(raw, headers={"User-Agent": "Mozilla/5.0 (compatible; Astralis/1.0)"})
                    with urlopen(request, timeout=15) as response:
                        mime = response.headers.get_content_type()
                        if not mime.startswith("image/"): raise ValueError("La ressource n’est pas une image.")
                        payload = response.read(8 * 1024 * 1024 + 1)
                    if len(payload) > 8 * 1024 * 1024: raise ValueError("Image trop volumineuse.")
                    with cache_lock: cache[key] = (now, payload)
                self.send_bytes(200, payload, mime); return
            except Exception as exc:
                self.send_json(502, {"error": "Image distante indisponible.", "detail": str(exc)}); return
        if path == "/api/gi/events":
            key = "gi/events"; now = time.time()
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < 3600 and not refresh else None
            if payload is None:
                try:
                    payload = genshin_events()
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "Le calendrier GenshinFlex est indisponible.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path in {"/api/gi/news", "/api/gi/tierlist"}:
            key = path.removeprefix("/api/")
            now = time.time()
            ttl = 1800 if path.endswith("/news") else 3600
            with cache_lock:
                entry = cache.get(key); payload = entry[1] if entry and now-entry[0] < ttl and not refresh else None
            if payload is None:
                try:
                    payload = genshin_news() if path.endswith("/news") else genshin_tierlist_status()
                    with cache_lock: cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La source est momentanément indisponible.", "detail": str(exc)}); return
            self.send_bytes(200, payload, "application/json; charset=utf-8"); return
        if path == "/api/gi/endgame":
            key = "gi/endgame"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                stale_payload = entry[1] if entry else None
                payload = entry[1] if entry and now - entry[0] < TTL and not refresh else None
            if payload is None:
                try:
                    payload = genshin_endgame()
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    if stale_payload:
                        payload = stale_payload
                    else:
                        self.send_json(502, {"error": "La source Endgame est indisponible.", "detail": str(exc)})
                        return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        public_profile = re.fullmatch(r"/api/gi/profile/(\d{8,10})", path)
        if public_profile:
            uid = public_profile.group(1)
            key = f"gi/profile/{uid}"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                payload = entry[1] if entry and now - entry[0] < TTL and not refresh else None
            if payload is None:
                try:
                    payload = fetch(f"https://enka.network/api/uid/{uid}/")
                    if len(payload) > 2 * 1024 * 1024:
                        raise ValueError("La réponse du profil dépasse la limite de 2 Mo.")
                    json.loads(payload)
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "Profil public Enka indisponible ou non public.", "detail": str(exc)})
                    return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        detail = re.fullmatch(r"/detail/gi/character/([a-z0-9-]+)", path)
        if detail:
            slug = detail.group(1)
            key = f"gi/detail/{slug}"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                payload = entry[1] if entry and now - entry[0] < TTL else None
            if payload is None:
                try:
                    payload = fetch(f"https://genshin.jmp.blue/characters/{slug}?lang=fr")
                    json.loads(payload)
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La fiche détaillée ne répond pas.", "detail": str(exc)})
                    return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        talent_detail = re.fullmatch(r"/detail/gi/talents/([a-z0-9-]+)", path)
        if talent_detail:
            slug = talent_detail.group(1)
            key = f"gi/talents/{slug}"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                payload = entry[1] if entry and now - entry[0] < TTL else None
            if payload is None:
                try:
                    query = "Traveler" if slug.startswith("traveler") else slug
                    url = f"https://genshin-db-api.vercel.app/api/v5/talents?query={query}&matchCategories=true&dumpResult=true&queryLanguages=french&resultLanguage=French"
                    response = json.loads(fetch(url))
                    result = response.get("result") or {}
                    if not result.get("combat1"):
                        raise ValueError("Aucune table de talents trouvée pour ce personnage.")
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La table des talents ne répond pas.", "detail": str(exc)})
                    return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        detail = re.fullmatch(r"/detail/ww/character/([a-z0-9-]+)", path)
        if detail:
            slug = detail.group(1)
            key = f"ww/detail/{slug}"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                payload = entry[1] if entry and now - entry[0] < TTL else None
            if payload is None:
                try:
                    if slug.isdigit():
                        source = json.loads(fetch(f"https://api-v2.encore.moe/api/en/character/{slug}?v=Beta"))
                        skills = []
                        for skill in source.get("Skills", []):
                            name = skill.get("SkillName") or skill.get("SkillType") or "Compétence"
                            values = []
                            for attribute in skill.get("SkillAttributes", []):
                                levels = attribute.get("values") or []
                                if levels:
                                    values.append(f"{attribute.get('attributeName', 'Valeur')} : {levels[min(9, len(levels)-1)]}")
                            skills.append({
                                "id": str(skill.get("SkillId", name)), "name": name,
                                "label": skill.get("SkillType") or "Compétence",
                                "description": html_text(skill.get("SkillDescribe", "")),
                                "icon": skill.get("Icon", ""), "values": values,
                            })
                        chains = [{
                            "name": f"C{int(row.get('GroupIndex') or i + 1)} · {row.get('NodeName') or 'Résonance'}",
                            "description": html_text(row.get("AttributesDescription", "")),
                            "icon": row.get("NodeIcon", ""),
                        } for i, row in enumerate(source.get("ResonantChain", []))]
                        artworks = list(dict.fromkeys(value for value in (
                            source.get("Card"), source.get("FormationRoleCard"), source.get("RolePortrait"),
                            source.get("RoleStand"), source.get("RoleHeadIconLarge"),
                        ) if value))
                        portrait = source.get("RolePortrait") or source.get("RoleHeadIconLarge") or source.get("Card") or ""
                        payload = json.dumps({
                            "portraitUrl": portrait, "artworks": artworks, "skills": skills, "constellations": chains,
                            "baseStats": [{"name": row.get("Name", ""), "value": row.get("BaseValue", ""), "icon": row.get("Icon", "")} for row in source.get("Properties", [])],
                            "source": "Encore API · données Beta",
                        }, ensure_ascii=False).encode("utf-8")
                    else:
                        markup = fetch(f"{BASE}/en/characters/{slug}").decode("utf-8", errors="replace")
                        portrait_match = re.search(r'<img\b[^>]*alt="[^"]+ portrait"[^>]*src="([^"]+)"', markup, flags=re.I)
                        portrait = unescape(portrait_match.group(1)).replace("/_ipx/q_70&s_180x180/", "/") if portrait_match else ""
                        skills = []
                        cards = re.findall(r'<div class="rounded-md border border-border/50 p-4">(.*?)</div>', markup, flags=re.I | re.S)
                        for index, card in enumerate(cards[:8]):
                            heading = re.search(r"<h3\b[^>]*>(.*?)</h3>", card, flags=re.I | re.S)
                            paragraph = re.search(r"<p\b[^>]*>(.*?)</p>", card, flags=re.I | re.S)
                            badge = re.search(r'<span\b[^>]*data-slot="badge"[^>]*>(.*?)</span>', card, flags=re.I | re.S)
                            if heading:
                                skills.append({
                                    "id": f"ww-{index}", "name": html_text(heading.group(1)),
                                    "label": html_text(badge.group(1)) if badge else "Compétence",
                                    "description": html_text(paragraph.group(1)) if paragraph else "",
                                    "glyph": ["⚔", "◈", "✦", "◎", "↗", "◇"][index % 6],
                                })
                        payload = json.dumps({"portraitUrl": portrait, "skills": skills}, ensure_ascii=False).encode("utf-8")
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La fiche WutheringDB ne répond pas.", "detail": str(exc)})
                    return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        match = re.fullmatch(r"/data/(hsr|gi|ww)/(character|weapon|artifact|skills)", path)
        if match:
            game, category = match.groups()
            key = f"{game}/{category}"
            now = time.time()
            with cache_lock:
                entry = cache.get(key)
                if not refresh and entry and now - entry[0] < TTL:
                    payload = entry[1]
                else:
                    payload = None
            if payload is None:
                try:
                    if game == "ww":
                        payload = wuthering_cards(category)
                    else:
                        url = SOURCES[(game, category)]
                        if game == "gi":
                            url += "?lang=fr"
                        payload = fetch(url)
                    json.loads(payload)
                    with cache_lock:
                        cache[key] = (now, payload)
                except Exception as exc:
                    self.send_json(502, {"error": "La source distante ne répond pas.", "detail": str(exc)})
                    return
            self.send_bytes(200, payload, "application/json; charset=utf-8")
            return
        super().do_GET()

    def send_json(self, status: int, data: object) -> None:
        self.send_bytes(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def send_bytes(self, status: int, payload: bytes, mime: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", f"public, max-age={TTL}" if mime.startswith("application/json") else "no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    if os.environ.get("RENDER") and len(os.environ.get("ASTRALIS_PASSWORD", "")) < 16:
        raise RuntimeError("Définis ASTRALIS_PASSWORD avec au moins 16 caractères dans les variables Render.")
    print(f"Astralis lancé sur http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


