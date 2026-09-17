"""
Passo 3: unire le finestre, togliere i campi vuoti, fondere i doppioni.

Le finestre si sovrappongono e la prof torna sugli stessi argomenti a
distanza di settimane, quindi la stessa voce puo' uscire piu' volte. La
chiave di fusione e' il lemma normalizzato (o l'insieme degli elementi per
le coppie, o il titolo per le regole).
"""

import json
import re
import unicodedata
from collections import Counter

FILES = [
    "estrazione_blocchi_0_96.json",
    "estrazione_blocchi_96_260.json",
    "estrazione_blocchi_261_400.json",
    "estrazione_seconda_passata.json",
]


PLACEHOLDER = re.compile(
    r"\b(somebody|someone|something|sth|sb|one's|oneself|smth)\b")


def slug(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'")
    # "to look forward to something" e "look forward to" sono la stessa voce:
    # i segnaposto e gli articoli non devono impedire la fusione.
    s = PLACEHOLDER.sub(" ", s)
    s = re.sub(r"^(to|a|an|the)\s+", "", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def key(v):
    if v["tipo"] == "scarto":
        return None
    if "elementi" in v:
        return "coppia:" + "|".join(sorted(slug(x) for x in v["elementi"]))
    if v["tipo"] in ("regola", "lettura"):
        return v["tipo"] + ":" + slug(v.get("titolo"))
    return "voce:" + slug(v.get("lemma"))


def clean(v):
    """Toglie i campi vuoti e normalizza i default impliciti."""
    out = {k: val for k, val in v.items()
           if val not in (None, "", [], {})}
    if out.get("tipo") not in ("scarto", "lettura", "regola", "gruppo_trattenuto"):
        out.setdefault("direzione", "en>it")
    # L'IPA su una frase lunga non serve a nessuno.
    target = out.get("lemma") or " ".join(out.get("elementi", []))
    if out.get("ipa") and len(target.split()) > 3 and "·" not in out["ipa"]:
        del out["ipa"]
    # Un esempio identico al lemma non e' un esempio.
    if out.get("esempi"):
        ex = [e for e in out["esempi"] if slug(e) != slug(out.get("lemma"))]
        if ex:
            out["esempi"] = ex
        else:
            del out["esempi"]
    # Se la traduzione ripete quella della prof, ne basta una.
    if slug(out.get("traduzione")) and slug(out.get("traduzione")) == slug(out.get("traduzione_prof")):
        del out["traduzione"]
    return out


def merge(a, b):
    """Fonde due occorrenze della stessa voce tenendo la piu' ricca."""
    winner, other = (a, b) if len(json.dumps(a)) >= len(json.dumps(b)) else (b, a)
    winner["blocchi"] = sorted(set(winner.get("blocchi", []) + other.get("blocchi", [])))
    for f in ("esempi", "immagini"):
        if other.get(f):
            winner[f] = list(dict.fromkeys(winner.get(f, []) + other[f]))
    # Se una delle due era in attesa, resta in attesa: prudenza.
    if "in_attesa" in (a.get("stato"), b.get("stato")):
        winner["stato"] = "in_attesa"
    winner["confidenza"] = max(a.get("confidenza", 0), b.get("confidenza", 0))
    return winner


def consolida_per_blocchi(voci, tolleranza=8):
    """Regole e letture spezzate dalle finestre.

    Una finestra vede solo il suo pezzo di articolo o di regola, e lo
    intitola a modo suo: per questo la chiave sul titolo non le riunisce.
    Due voci dello stesso tipo che si sovrappongono sono la stessa cosa
    vista due volte; e per le letture basta che siano vicine, perche' un
    articolo spezzato lascia qualche riga di appunti in mezzo.
    """
    fusi = 0
    for tipo in ("regola", "lettura"):
        gap = tolleranza if tipo == "lettura" else 0
        gruppo = [v for v in voci if v["tipo"] == tipo]
        altri = [v for v in voci if v["tipo"] != tipo]
        risultato = []
        for v in gruppo:
            b = set(v.get("blocchi", []))
            for i, r in enumerate(risultato):
                rb = set(r.get("blocchi", []))
                if not b or not rb:
                    continue
                distanza = max(min(b) - max(rb), min(rb) - max(b))
                # Sovrapposte: stessa cosa vista da due finestre.
                # Oppure vicine, ma solo se una delle due e' un frammento
                # orfano: due articoli diversi possono stare a due righe di
                # distanza, e non vanno mai uniti.
                orfano = min(len(b), len(rb)) <= 2
                if (b & rb) or (gap and orfano and distanza <= gap):
                    risultato[i] = merge(r, v)
                    fusi += 1
                    break
            else:
                risultato.append(v)
        voci = altri + risultato
    return voci, fusi


def collega_termini_a_coppie(voci):
    """Il modello emette spesso il termine da solo E la coppia che lo contiene.

    Quando il termine isolato non aggiunge nulla alla coppia lo assorbiamo;
    se invece porta un significato suo (throttle sostantivo contro to
    throttle verbo) restano due voci, collegate fra loro.
    """
    coppie = {}
    for v in voci:
        for e in v.get("elementi", []):
            coppie.setdefault(slug(e), []).append(v)

    assorbiti, collegati, out = 0, 0, []
    for v in voci:
        s = slug(v.get("lemma"))
        ospiti = coppie.get(s) if s and "elementi" not in v else None
        if not ospiti:
            out.append(v)
            continue
        coppia = ospiti[0]
        if v["tipo"] == "termine" and len(v.get("definizione", "")) < 80:
            for f in ("esempi", "immagini"):
                if v.get(f):
                    coppia[f] = list(dict.fromkeys(coppia.get(f, []) + v[f]))
            coppia["blocchi"] = sorted(set(coppia.get("blocchi", []) + v.get("blocchi", [])))
            assorbiti += 1
            continue
        v["vedi_anche"] = "/".join(coppia["elementi"])
        collegati += 1
        out.append(v)
    return out, assorbiti, collegati


def run(files=None):
    files = files or FILES
    voci, fusioni = {}, 0
    scarti = []

    for f in files:
        for v in json.load(open(f, encoding="utf-8")):
            v = clean(v)
            if v["tipo"] == "scarto":
                scarti += v.get("blocchi", [])
                continue
            k = key(v)
            if k in voci:
                voci[k] = merge(voci[k], v)
                fusioni += 1
            else:
                voci[k] = v

    lista = list(voci.values())
    lista, fusi_blocchi = consolida_per_blocchi(lista)
    lista, assorbiti, collegati = collega_termini_a_coppie(lista)
    fusioni += fusi_blocchi + assorbiti

    finali = sorted(lista, key=lambda v: min(v.get("blocchi", [999])))
    json.dump(finali, open("dizionario.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    blocchi = json.load(open("blocks.json", encoding="utf-8"))
    tutti = {b["idx"] for b in blocchi}
    coperti = {i for v in finali for i in v.get("blocchi", [])} | set(scarti)

    print(f"voci finali        : {len(finali)}")
    for k, n in Counter(v["tipo"] for v in finali).most_common():
        print(f"   {k:>18}: {n}")
    print(f"fusioni applicate  : {fusioni}"
          f"  (di cui {fusi_blocchi} per blocchi condivisi, {assorbiti} termini in coppia)")
    print(f"termini collegati  : {collegati}")
    print(f"in attesa          : {sum(1 for v in finali if v.get('stato') == 'in_attesa')}")
    print(f"con divergenza     : {sum(1 for v in finali if v.get('divergenza'))}")
    print(f"copertura blocchi  : {len(coperti & tutti)}/{len(tutti)} "
          f"({len(coperti & tutti) * 100 // len(tutti)}%)")
    print(f"scoperti           : {sorted(tutti - coperti)}")

    campi = sum(len(v) for v in finali)
    print(f"campi per voce     : {campi / len(finali):.1f}")


if __name__ == "__main__":
    import sys
    run(sys.argv[1:] or None)
