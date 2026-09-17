"""
Passo 4: normalizzare i lemmi. In due tempi, di proposito.

  python normalize.py dizionario.json            propone -> fusioni.json
  python normalize.py dizionario.json --applica  applica fusioni.json

La prima versione di questo script mandava al modello i soli lemmi, per
risparmiare token, e applicava subito il risultato. Ha fuso suitcase con
luggage, trunk, trolley e carry-on, e to fold con unfold. Senza le glosse
il modello poteva solo raggruppare per argomento; senza revisione, il danno
finiva dritto nel dizionario.

Ora le glosse ci sono e l'applicazione e' un passo separato: fondere due
voci distrugge contenuto, e va guardato da un essere umano.
"""

import json
import re
import os
import sys

import anthropic

from merge import merge, slug
from parsing import json_array

MODEL = os.environ.get("EXTRACT_MODEL", "claude-sonnet-4-6")
PROPOSTE = "fusioni.json"
MAX_VARIANTI = 3

ISTRUZIONI = """Ecco i lemmi di un dizionario di inglese per studenti
italiani, ognuno con la sua glossa. Alcuni sono la STESSA voce scritta in
modo diverso, e vanno riuniti.

Restituisci SOLO un array JSON:

  [{"canonico": "...", "varianti": ["..."], "perche": "in dieci parole"}]

Fondi solo quando si tratta della stessa identica espressione formulata
diversamente:
  "bucket list" e "at the top of one's bucket list"  -> stessa voce
  "what's on your agenda" e "what's on your agenda for today?" -> stessa voce

NON fondere mai, per nessun motivo:

- CONTRARI: to pack e to unpack, to fold e unfold, tidy e untidy sono voci
  opposte, non varianti. Il prefisso un- ribalta il significato.
- PAROLE DELLO STESSO ARGOMENTO: suitcase, luggage, trunk, trolley,
  carry-on e sports bag riguardano tutte i bagagli e sono sei voci diverse.
  Appartenere allo stesso campo non e' essere la stessa parola.
- UN TERMINE E IL SUO COLLETTIVO: luggage non e' suitcase.
- SENSI DIVERSI DELLA STESSA RADICE: to iron (stirare) e iron supplements
  (integratori di ferro); throttle (acceleratore) e to throttle
  (strangolare); interest (interesse) e to lose interest.
- PAROLE IMPARENTATE MA NON EQUIVALENTI: to die non e' to kill oneself.

Nel dubbio non fondere: due voci simili sono un difetto lieve, due voci
diverse schiacciate in una sono contenuto perduto.

Il canonico e' la forma da dizionario e deve essere uno dei lemmi
dell'elenco: verbo all'infinito con to, sostantivo singolare, senza
possessivi e senza contesto. Al massimo tre varianti per gruppo. Ometti del
tutto le voci senza doppioni.
"""


def glossa(v):
    g = (v.get("traduzione") or v.get("traduzione_prof")
         or v.get("definizione") or "")
    return re.sub(r"\s+", " ", g)[:90]


def proponi(percorso):
    voci = json.load(open(percorso, encoding="utf-8"))
    righe, visti = [], set()
    for v in voci:
        l = v.get("lemma")
        if not l or slug(l) in visti:
            continue
        visti.add(slug(l))
        g = glossa(v)
        righe.append(f"{l} - {g}" if g else l)

    print(f"lemmi da esaminare: {len(righe)}")
    if not os.environ.get('ANTHROPIC_API_KEY'):
        raise SystemExit('Manca ANTHROPIC_API_KEY.')
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=4000,
        messages=[{"role": "user",
                   "content": ISTRUZIONI + "\n\n" + "\n".join(righe)}],
    )
    gruppi = json_array("".join(p.text for p in msg.content if p.type == "text"))

    reali = {slug(v["lemma"]) for v in voci if v.get("lemma")}
    puliti = []
    for g in gruppi:
        can = g.get("canonico")
        var = [v for v in g.get("varianti", [])
               if slug(v) in reali and slug(v) != slug(can)][:MAX_VARIANTI]
        if can and slug(can) in reali and var:
            puliti.append({"canonico": can, "varianti": var,
                           "perche": g.get("perche", "")})

    json.dump(puliti, open(PROPOSTE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"\n{len(puliti)} fusioni proposte -> {PROPOSTE}\n")
    for g in puliti:
        print(f"  {g['canonico']:<30} <- {', '.join(g['varianti'])}")
        if g["perche"]:
            print(f"  {'':<30}    ({g['perche']})")
    print(f"\nApri {PROPOSTE}, CANCELLA i gruppi sbagliati, poi:")
    print(f"  python normalize.py {percorso} --applica")


def applica(percorso):
    voci = json.load(open(percorso, encoding="utf-8"))
    gruppi = json.load(open(PROPOSTE, encoding="utf-8"))

    mappa = {slug(v): g["canonico"] for g in gruppi for v in g["varianti"]}
    fuse, out = 0, {}
    for v in voci:
        s = slug(v.get("lemma"))
        if s in mappa:
            v = dict(v, lemma=mappa[s])
            s = slug(v["lemma"])
        chiave = s or json.dumps(v.get("elementi") or v.get("titolo"))
        if chiave in out:
            out[chiave] = merge(out[chiave], v)
            fuse += 1
        else:
            out[chiave] = v

    finali = sorted(out.values(), key=lambda v: min(v.get("blocchi", [999])))
    json.dump(finali, open(percorso, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"voci: {len(voci)} -> {len(finali)}  ({fuse} fuse)")


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "dizionario.json"
    if "--applica" in sys.argv:
        applica(doc)
    else:
        proponi(doc)
