"""
Passo 2: dai blocchi alle voci, chiamando il modello.

Tre cose che il prototipo ha insegnato e che qui sono codificate:

  1. il significato sta nel gruppo, non nella riga: le finestre si
     sovrappongono, altrimenti i gruppi a cavallo del taglio si perdono;
  2. una passata sola perde circa il 15% delle voci: la seconda passata
     rimanda al modello i soli blocchi rimasti scoperti;
  3. le euristiche possono scartare simboli e date, mai frasi: qui
     "scarto" significa solo cio' che nessun modello deve nemmeno vedere.
"""

import json
import os
import re
import time

import anthropic

from parsing import json_array

MODEL = os.environ.get("EXTRACT_MODEL", "claude-sonnet-4-6")
FINESTRA = 25          # blocchi per chiamata
SOVRAPPOSIZIONE = 5    # blocchi ripetuti fra una finestra e la successiva
MAI_INVIARE = {"scarto", "marcatore_data"}

PROMPT = open(os.path.join(os.path.dirname(__file__), "extract_prompt.md"),
              encoding="utf-8").read()

_client = None


def client():
    # Il client si crea alla prima chiamata, non all'importazione: cosi'
    # chi importa questo modulo senza dover estrarre nulla non ha bisogno
    # della chiave, e chi ce l'ha dimenticata riceve un messaggio chiaro.
    global _client
    if _client is None:
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise SystemExit(
                'Manca ANTHROPIC_API_KEY. Su Windows: set ANTHROPIC_API_KEY=sk-ant-...')
        _client = anthropic.Anthropic()
    return _client


def _finestre(blocks, dim=FINESTRA, ov=SOVRAPPOSIZIONE):
    utili = [b for b in blocks if b.kind not in MAI_INVIARE]
    passo = dim - ov
    for i in range(0, len(utili), passo):
        gruppo = utili[i:i + dim]
        if gruppo:
            yield gruppo
        if i + dim >= len(utili):
            break


def _rendi(blocks):
    """I blocchi come li vede il modello: indice, tipo presunto, testo."""
    righe = []
    for b in blocks:
        marca = " [IMMAGINE]" if b.images else ""
        if b.kind == "lettura":
            marca += " [TESTO LUNGO]"
        righe.append(f"[{b.idx}]{marca} {b.text}")
    return "\n".join(righe)


def _chiama(blocks, coda=""):
    msg = client().messages.create(
        model=MODEL,
        max_tokens=8000,
        system=PROMPT,
        messages=[{"role": "user", "content": _rendi(blocks) + coda}],
    )
    return json_array("".join(p.text for p in msg.content if p.type == "text"))


def estrai(blocks, verbose=True):
    voci = []
    for n, gruppo in enumerate(_finestre(blocks), 1):
        if verbose:
            print(f"  finestra {n}: blocchi {gruppo[0].idx}-{gruppo[-1].idx}")
        voci += _chiama(gruppo)
        time.sleep(0.5)

    # Seconda passata: cosa e' rimasto fuori?
    inviabili = {b.idx for b in blocks if b.kind not in MAI_INVIARE}
    coperti = {i for v in voci for i in v.get("blocchi", [])}
    rimasti = sorted(inviabili - coperti)

    if rimasti:
        if verbose:
            print(f"  seconda passata su {len(rimasti)} blocchi scoperti")
        per_idx = {b.idx: b for b in blocks}
        coda = ("\n\nQuesti blocchi non sono finiti in nessuna voce alla prima "
                "lettura. Rileggili: contengono qualcosa da estrarre, oppure "
                "sono davvero scarto? Se una voce esiste gia' altrove, "
                "riproducila con i soli campi tipo, lemma (o elementi) e "
                "blocchi, cosi' viene fusa.")
        for i in range(0, len(rimasti), FINESTRA):
            gruppo = [per_idx[x] for x in rimasti[i:i + FINESTRA]]
            voci += _chiama(gruppo, coda)
            time.sleep(0.5)

    return voci


if __name__ == "__main__":
    import sys
    from prep import prepare

    sorgente = sys.argv[1]
    creds = os.environ.get("GOOGLE_CREDENTIALS_FILE")

    blocks = prepare(sorgente, creds)
    print(f"blocchi: {len(blocks)}")

    voci = estrai(blocks)
    json.dump(voci, open("voci_grezze.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"voci grezze: {len(voci)} -> voci_grezze.json")
    print("ora: python3 merge.py")
