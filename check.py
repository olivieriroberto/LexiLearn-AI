"""
Diagnostica: le 201 voci sono doppioni o sono voci vere?

Non modifica niente. Stampa un rapporto corto da incollare in chat.
Uso:  python check.py dizionario.json riferimento.json
"""

import json
import sys
from collections import defaultdict

from merge import slug, key


def carica(p):
    return json.load(open(p, encoding="utf-8"))


def nome(v):
    return v.get("lemma") or v.get("titolo") or "/".join(v.get("elementi", []))


def run(nuovo, riferimento=None):
    d = carica(nuovo)

    print(f"=== {nuovo}: {len(d)} voci ===\n")

    # 1. Letture: quante sono e quanti blocchi coprono
    print("-- letture --")
    for v in d:
        if v["tipo"] == "lettura":
            b = v.get("blocchi", [])
            print(f"  {nome(v)[:45]:<45} blocchi {min(b) if b else '?'}-"
                  f"{max(b) if b else '?'} ({len(b)})")

    # 2. Voci il cui lemma e' contenuto in un altro: candidati alla fusione
    print("\n-- lemmi contenuti in altri (possibili doppioni) --")
    slugs = [(slug(nome(v)), nome(v)) for v in d if nome(v)]
    n = 0
    for s1, n1 in slugs:
        for s2, n2 in slugs:
            if s1 != s2 and len(s1) > 4 and f" {s1} " in f" {s2} ":
                print(f"  '{n1}'  dentro  '{n2}'")
                n += 1
    print(f"  totale: {n}")

    # 3. Voci che condividono la prima parola: famiglie non fuse
    print("\n-- gruppi con la stessa parola iniziale --")
    fam = defaultdict(list)
    for v in d:
        s = slug(nome(v))
        if s:
            fam[s.split()[0]].append(nome(v))
    for k, vs in sorted(fam.items()):
        if len(vs) > 2:
            print(f"  {k}: {', '.join(vs[:6])}")

    # 4. Quante voci pescano dentro i blocchi degli articoli
    letture = {i for v in d if v["tipo"] == "lettura" for i in v.get("blocchi", [])}
    dentro = [v for v in d if v["tipo"] != "lettura"
              and set(v.get("blocchi", [])) & letture]
    print(f"\n-- voci estratte da dentro gli articoli: {len(dentro)} --")
    for v in dentro[:15]:
        print(f"  {nome(v)}")

    # 5. Confronto col riferimento
    if riferimento:
        r = carica(riferimento)
        kn = {key(v) for v in d if key(v)}
        kr = {key(v) for v in r if key(v)}
        print(f"\n-- confronto con {riferimento} --")
        print(f"  in comune        : {len(kn & kr)}")
        print(f"  solo nel nuovo   : {len(kn - kr)}")
        print(f"  solo nel mio     : {len(kr - kn)}")
        mancanti = [nome(v) for v in r if key(v) in kr - kn]
        print(f"  che ho io e manca al nuovo: {', '.join(mancanti[:25])}")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
