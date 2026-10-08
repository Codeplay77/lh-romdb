"""Gera romdb.db.gz + version.json a partir do banco do Romgi, mantendo só os consoles do LightHouse.

Uso: python scripts/filter_romgi.py caminho/romdb.db.gz [pasta_saida]   (padrão: raiz do repositório)

O banco continua no formato original do Romgi (SQLite, schema v4): só remove os consoles
fora da lista e junta o New 3DS ao 3DS.
"""
import datetime
import gzip
import json
import os
import shutil
import sqlite3
import sys
import tempfile

KEEP = ["nes", "snes", "gb", "gbc", "gba", "n64", "nds", "3ds", "gc", "wii", "wiiu", "switch",
        "sms", "smd", "scd", "32x", "sat", "dc", "ps1", "ps2", "psp", "ps3", "psv", "xbox", "x360"]
MERGE = {"n3ds": "3ds"}
EXTRA_PLATFORMS = [("switch", "Nintendo", "Nintendo Switch")]

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT
    work = os.path.join(tempfile.gettempdir(), "romdb_filter.db")
    opener = gzip.open if src.endswith(".gz") else open
    with opener(src, "rb") as s, open(work, "wb") as d:
        shutil.copyfileobj(s, d)

    db = sqlite3.connect(work)
    for old, new in MERGE.items():
        db.execute("UPDATE entries SET platform=? WHERE platform=?", (new, old))
        db.execute("UPDATE entry_groups SET platform=? WHERE platform=?", (new, old))
    for pid, brand, name in EXTRA_PLATFORMS:
        db.execute("INSERT OR IGNORE INTO platforms (id, brand, name) VALUES (?,?,?)", (pid, brand, name))

    marks = ",".join("?" * len(KEEP))
    db.execute(f"CREATE TEMP TABLE gone AS SELECT slug FROM entries WHERE platform NOT IN ({marks})", KEEP)
    db.execute("DELETE FROM links WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM regions_entries WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entry_group_members WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entries WHERE slug IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entry_groups WHERE id NOT IN (SELECT group_id FROM entry_group_members)")
    db.execute(f"DELETE FROM entry_groups WHERE platform IS NOT NULL AND platform NOT IN ({marks})", KEEP)
    db.execute(f"DELETE FROM platforms WHERE id NOT IN ({marks})", KEEP)
    db.execute("DELETE FROM torrents WHERE infohash NOT IN "
               "(SELECT DISTINCT torrent_infohash FROM links WHERE torrent_infohash IS NOT NULL)")
    db.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
    db.commit()
    db.execute("VACUUM")

    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("entries", "links", "platforms", "sources")}
    db.close()

    gz = os.path.join(out, "romdb.db.gz")
    with open(work, "rb") as s, gzip.open(gz, "wb", compresslevel=9) as d:
        shutil.copyfileobj(s, d)

    now = datetime.datetime.now(datetime.timezone.utc)
    version = {
        "version": now.strftime("%Y%m%d%H%M"),
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": 4,
        "size": os.path.getsize(gz),
        "uncompressed_size": os.path.getsize(work),
        **counts,
    }
    with open(os.path.join(out, "version.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(version, f, indent=2)
        f.write("\n")
    os.remove(work)
    print(f"OK: {counts['entries']} jogos, {counts['links']} links, {counts['platforms']} consoles -> "
          f"{gz} ({version['size'] // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
