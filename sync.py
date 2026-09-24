"""
Il pezzo che rende il sistema utilizzabile davvero: sincronizzare senza
rifare tutto.

  python sync.py                    usa DOC_ID dall'ambiente
  python sync.py appunti.docx       prova in locale su un file
  python sync.py --forza            rilegge tutto da capo

Tre filtri in cascata, dal piu' economico al piu' caro:

  1. la data di modifica del documento: se non e' cambiata, fine.
  2. gli hash dei blocchi: al modello vanno solo quelli mai visti.
  3. la fusione: le voci nuove si innestano su quelle esistenti.

Lo stato vive in stato.json, che nel flusso automatico viene riscritto nel
repository a ogni giro: e' la memoria fra un'esecuzione e l'altra.
"""

import json
import os
import sys
from datetime import datetime, timezone

import merge
import prep
import sito

STATO = "stato.json"
DIZIONARIO = "dizionario.json"
NUOVE = "voci_nuove.json"
CONTESTO = 5   # blocchi gia' noti mandati come cornice di quelli nuovi


def segna_data_ingresso(prima):
    """Mette la data di oggi sulle voci che non c'erano al giro precedente.

    Una voce marcata una volta non cambia piu' data: `aggiunta` e' il giorno
    in cui e' entrata nel dizionario, non l'ultima volta che e' stata
    toccata. Le voci dello storico restano senza data e finiscono in fondo
    all'ordinamento cronologico.
    """
    voci = json.load(open(DIZIONARIO, encoding="utf-8"))
    oggi = datetime.now(timezone.utc).date().isoformat()
    nuove = 0
    for v in voci:
        k = merge.key(v)
        if k and k not in prima and not v.get("aggiunta"):
            v["aggiunta"] = oggi
            nuove += 1
    if nuove:
        json.dump(voci, open(DIZIONARIO, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return nuove


def carica_stato():
    if os.path.exists(STATO):
        return json.load(open(STATO, encoding="utf-8"))
    return {"modificato": None, "hash_visti": [], "giri": []}


def salva_stato(stato, blocks, nuove):
    stato["hash_visti"] = sorted({b.hash for b in blocks}
                                 | set(stato.get("hash_visti", [])))
    stato["giri"] = (stato.get("giri", []) + [{
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "blocchi_nuovi": len(nuove),
    }])[-20:]
    json.dump(stato, open(STATO, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def sincronizza(sorgente=None, forza=False):
    sorgente = sorgente or os.environ.get("DOC_ID")
    creds = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    if not sorgente:
        sys.exit("Manca DOC_ID (o il percorso di un .docx come argomento).")

    stato = carica_stato()

    # --- filtro 1: la data di modifica -------------------------------------
    if not sorgente.lower().endswith(".docx"):
        modificato, titolo = prep.doc_last_modified(sorgente, creds)
        print(f"documento: {titolo}")
        print(f"ultima modifica: {modificato}")
        if not forza and modificato == stato.get("modificato"):
            print("nessuna modifica dall'ultimo giro: non c'e' niente da fare.")
            return False
        stato["modificato"] = modificato

    # --- filtro 2: gli hash dei blocchi ------------------------------------
    blocks = prep.prepare(sorgente, creds)

    # Il sito prende da qui il testo integrale degli articoli: senza questo
    # file, nel flusso automatico le letture uscirebbero vuote.
    json.dump([vars(b) for b in blocks], open("blocks.json", "w",
              encoding="utf-8"), ensure_ascii=False, indent=1)

    visti = set() if forza else set(stato.get("hash_visti", []))
    nuovi = [b for b in blocks if b.hash not in visti]
    print(f"blocchi: {len(blocks)} totali, {len(nuovi)} mai visti")

    if not nuovi:
        salva_stato(stato, blocks, [])
        print("il documento e' cambiato ma nessun blocco e' nuovo "
              "(riordini o ritocchi): niente da estrarre.")
        return False

    # Ai blocchi nuovi si affiancano alcuni vicini gia' noti: una voce nasce
    # quasi sempre da un gruppo di righe, e senza cornice il modello vede
    # meta' dei gruppi tagliata.
    indici = {b.idx for b in nuovi}
    for b in nuovi:
        for i in range(b.idx - CONTESTO, b.idx + CONTESTO + 1):
            indici.add(i)
    finestra = [b for b in blocks if b.idx in indici]
    print(f"inviati al modello: {len(finestra)} (con {CONTESTO} di cornice)")

    # --- estrazione e fusione ---------------------------------------------
    # Importato qui e non in testa: serve solo quando c'e' da estrarre.
    from extract import estrai

    voci = estrai(finestra)
    json.dump(voci, open(NUOVE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"voci grezze: {len(voci)}")

    # Di quali voci il dizionario disponeva PRIMA di questo giro: serve a
    # riconoscere dopo la fusione quelle appena nate. La posizione nel
    # documento non e' un indizio utile (la prof scrive dove capita, anche
    # in cima), mentre la data di ingresso la decidiamo noi ed e' esatta.
    esistenti = DIZIONARIO if os.path.exists(DIZIONARIO) else None
    prima = set()
    if esistenti:
        for v in json.load(open(DIZIONARIO, encoding="utf-8")):
            if merge.key(v):
                prima.add(merge.key(v))

    merge.run([esistenti, NUOVE] if esistenti else [NUOVE])
    nuove = segna_data_ingresso(prima)
    print(f"voci mai viste prima: {nuove}")

    sito.genera(DIZIONARIO, "dizionario.html")
    salva_stato(stato, blocks, nuovi)
    return True


if __name__ == "__main__":
    argomenti = [a for a in sys.argv[1:] if not a.startswith("--")]
    sorgente = argomenti[0] if argomenti else None

    if "--segna-visto" in sys.argv:
        # Il dizionario esiste gia' ma lo stato no: senza questo, il primo
        # giro rifarebbe l'estrazione di tutto il documento.
        fonte = sorgente or os.environ.get("DOC_ID")
        blocks = prep.prepare(fonte, os.environ.get("GOOGLE_CREDENTIALS_FILE"))
        stato = carica_stato()
        if not fonte.lower().endswith(".docx"):
            stato["modificato"] = prep.doc_last_modified(
                fonte, os.environ.get("GOOGLE_CREDENTIALS_FILE"))[0]
        salva_stato(stato, blocks, [])
        sys.exit(f"{len(blocks)} blocchi segnati come gia' elaborati.")

    cambiato = sincronizza(sorgente, forza="--forza" in sys.argv)
    # Codice 0 comunque: "nessuna modifica" non e' un errore.
    print("aggiornato." if cambiato else "invariato.")
