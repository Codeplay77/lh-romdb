# lh-romdb

Catálogo de jogos do LightHouse no formato original do Romgi (SQLite, schema v4), versionado aqui para não depender do repositório do Romgi.

| Arquivo | Conteúdo |
|---|---|
| `romdb.db.gz` | Banco SQLite compactado (o que o app baixa) |
| `version.json` | Versão e contagens; o app usa para validar o schema |
| `scripts/filter_romgi.py` | Gera os dois arquivos a partir de um banco do Romgi, só com os consoles do LH |

Consoles: NES, SNES, Game Boy, Game Boy Color, GBA, N64, DS, 3DS (inclui New 3DS), GameCube, Wii, Wii U, Switch, Master System, Mega Drive, Sega CD, 32X, Saturn, Dreamcast, PS1, PS2, PSP, PS3, PS Vita, Xbox, Xbox 360.

## Editar

1. Descompacte: `python -c "import gzip,shutil;shutil.copyfileobj(gzip.open('romdb.db.gz'),open('romdb.db','wb'))"`
2. Abra `romdb.db` no [DB Browser for SQLite](https://sqlitebrowser.org) e edite `entries` (títulos, capas), `links` (downloads) e `sources` (`priority` menor = tentada primeiro).
3. Se mexer em `title`/`search_key`, rode `INSERT INTO entries_fts(entries_fts) VALUES('rebuild');`.
4. Recompacte com `python scripts/filter_romgi.py romdb.db .` (refiltra, recompacta e atualiza `version.json`), apague o `romdb.db` e faça commit.

## No LightHouse

`romgi_catalog_url = https://raw.githubusercontent.com/<usuario>/lh-romdb/main` no `lighthouse.conf` (já é o padrão do app).
