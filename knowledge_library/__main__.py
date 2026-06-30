"""Knowledge Library CLI.

    python -m knowledge_library add <kind> "<title>" [--body "..."] [--tags a,b] [--source "..."]
    python -m knowledge_library search "<query>"
    python -m knowledge_library list [--kind idea]
    python -m knowledge_library show <id>

kinds: note | article | source | idea | competitor
"""

from __future__ import annotations

import argparse
import sys

from core.console import enable_utf8_console
from knowledge_library.library import KnowledgeLibrary


def main(argv=None) -> int:
    enable_utf8_console()
    parser = argparse.ArgumentParser(prog="knowledge_library")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("kind"); a.add_argument("title")
    a.add_argument("--body", default=""); a.add_argument("--tags", default=""); a.add_argument("--source", default="")
    s = sub.add_parser("search"); s.add_argument("query")
    ls = sub.add_parser("list"); ls.add_argument("--kind")
    sh = sub.add_parser("show"); sh.add_argument("id")
    args = parser.parse_args(argv)

    lib = KnowledgeLibrary()
    if args.cmd == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        eid = lib.add(args.kind, args.title, body=args.body, tags=tags, source=args.source)
        print(f"Added {eid}")
        return 0
    if args.cmd == "search":
        hits = lib.search(args.query)
        if not hits:
            print("(no matches)")
        for e in hits:
            print(f"[{e['score']:>2}] {e['id']} ({e['kind']}) — {e['title']}")
        return 0
    if args.cmd == "list":
        for e in lib.list(kind=args.kind):
            print(f"{e['id']} ({e['kind']}) — {e['title']}")
        return 0
    if args.cmd == "show":
        e = lib.get(args.id)
        if not e:
            print("(not found)"); return 1
        print(f"{e['title']} ({e['kind']})\nsource: {e.get('source','')}\ntags: {', '.join(e.get('tags', []))}\n\n{e['body']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
