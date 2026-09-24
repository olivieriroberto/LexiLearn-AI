"""
Rende definitive le decisioni prese sulle voci trattenute.

Il sito e' una pagina statica: le approvazioni che fai da li' restano nel
browser di chi le ha prese, quindi non le vede nessun altro e spariscono se
si cancellano i dati del sito. Questo script le scrive nel dizionario, dove
sono permanenti e valgono per tutti.

  python approva.py --tutte        approva tutte le voci in attesa
  python approva.py decisioni.json applica il file scaricato dal sito
  python approva.py --elenca       mostra cosa e' in attesa, senza toccare nulla

Dopo, ricordati di mandare il dizionario aggiornato su GitHub:
  git add dizionario.json && git commit -m "Voci approvate" && git push
"""

import json
import sys

DIZIONARIO = "dizionario.json"


def nome(v):
    return v.get("lemma") or v.get("titolo") or "/".join(v.get("elementi", [])) \
        or ("Blocchi non estratti" if v.get("tipo") == "gruppo_trattenuto" else "")


def carica():
    return json.load(open(DIZIONARIO, encoding="utf-8"))


def elenca():
    attesa = [v for v in carica() if v.get("stato") == "in_attesa"]
    if not attesa:
        print("Nessuna voce in attesa.")
        return
    print(f"{len(attesa)} voci in attesa:\n")
    for v in attesa:
        print(f"  {nome(v)}")
        if v.get("note"):
            print(f"      {v['note'][:100]}")


def applica(decisioni=None, tutte=False):
    voci = carica()
    approvate, escluse = 0, []

    for v in voci:
        if v.get("stato") != "in_attesa":
            continue
        scelta = "approvata" if tutte else (decisioni or {}).get(nome(v))
        if scelta == "approvata":
            v["stato"] = "pubblicata"
            approvate += 1
        elif scelta == "esclusa":
            escluse.append(v)

    # Le voci escluse si tolgono davvero: lasciarle in attesa significa
    # ritrovarsele davanti a ogni giro.
    if escluse:
        voci = [v for v in voci if v not in escluse]

    json.dump(voci, open(DIZIONARIO, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    rimaste = sum(1 for v in voci if v.get("stato") == "in_attesa")
    print(f"approvate: {approvate}")
    print(f"eliminate: {len(escluse)}")
    print(f"ancora in attesa: {rimaste}")
    print("\nOra: git add dizionario.json && git commit -m "
          "\"Voci approvate\" && git push")


if __name__ == "__main__":
    argomenti = sys.argv[1:]
    if "--elenca" in argomenti:
        elenca()
    elif "--tutte" in argomenti:
        applica(tutte=True)
    elif argomenti:
        applica(json.load(open(argomenti[0], encoding="utf-8")))
    else:
        sys.exit(__doc__)
