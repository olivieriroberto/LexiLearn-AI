"""
Passo 1 della catena: leggere gli appunti e spezzarli in blocchi classificabili.

Nessuna chiamata all'AI qui dentro. Questo modulo fa solo il lavoro
deterministico: legge il documento conservando la formattazione, taglia in
blocchi, calcola un hash per ognuno e applica le euristiche che permettono
di NON mandare al modello cio' che non serve.

Il lettore e' volutamente isolato in read_docx(): quando passeremo all'API
di Google Docs si scrive read_gdoc() con la stessa firma e il resto della
catena non cambia di una riga.
"""

import hashlib
import re
from dataclasses import dataclass, field, asdict

import docx
from docx.oxml.ns import qn


# --- modello dati -----------------------------------------------------------

@dataclass
class Block:
    idx: int                        # posizione nel documento
    text: str                       # testo con marcatori di formattazione
    plain: str                      # testo nudo, per hash e confronti
    kind: str = "da_classificare"   # esito della pre-classificazione
    images: list = field(default_factory=list)   # hash delle immagini inline
    is_heading: bool = False
    has_emphasis: bool = False
    flags: list = field(default_factory=list)
    hash: str = ""

    def compute_hash(self):
        base = self.plain.lower() + "|" + "|".join(self.images)
        self.hash = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
        return self.hash


# --- lettura del sorgente ---------------------------------------------------

def _scomponi(t):
    """Separa gli spazi ai bordi dal testo vero: (prima, centro, dopo)."""
    centro = t.strip()
    taglio = t.index(centro) if centro else 0
    return t[:taglio], centro, t[taglio + len(centro):]


def _run_images(run, part):
    """Hash delle immagini contenute in un run, cosi' le elaboriamo una volta sola."""
    out = []
    for blip in run._element.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if not rid:
            continue
        try:
            blob = part.related_parts[rid].blob
        except KeyError:
            continue
        out.append(hashlib.sha1(blob).hexdigest()[:12])
    return out


def read_docx(path):
    """Restituisce la lista dei blocchi grezzi, nell'ordine del documento."""
    doc = docx.Document(path)
    blocks = []

    for i, para in enumerate(doc.paragraphs):
        pieces, images, emphasis = [], [], False

        for run in para.runs:
            images += _run_images(run, para.part)
            t = run.text
            if not t.strip():
                pieces.append(t)
                continue
            # La prof usa grassetto e corsivo per marcare cio' che conta:
            # e' un segnale, non decorazione. Va conservato.
            # Gli spazi ai bordi del run separano le parole: vanno tenuti
            # FUORI dai marcatori, altrimenti "Whether it's" diventa
            # "Whetherit's" e la parola sparisce dalla ricerca.
            pre, core, post = _scomponi(t)
            if run.bold:
                t, emphasis = f"{pre}**{core}**{post}", True
            elif run.italic:
                t, emphasis = f"{pre}*{core}*{post}", True
            pieces.append(t)

        text = re.sub(r"[ \t]+", " ", "".join(pieces)).strip()
        plain = re.sub(r"[*_]+", "", text).strip()

        if not plain and not images:
            continue

        b = Block(
            idx=i,
            text=text,
            plain=plain,
            images=images,
            is_heading=para.style.name.lower().startswith("heading"),
            has_emphasis=emphasis,
        )
        b.compute_hash()
        blocks.append(b)

    return blocks


# --- lettura da Google Docs -------------------------------------------------

DOC_SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _google_services(credentials_file):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=DOC_SCOPES)
    return (build("docs", "v1", credentials=creds),
            build("drive", "v3", credentials=creds))


def doc_last_modified(document_id, credentials_file):
    """Chiamata da pochi byte: dice solo se vale la pena leggere il documento."""
    _, drive = _google_services(credentials_file)
    meta = drive.files().get(fileId=document_id,
                             fields="modifiedTime,name").execute()
    return meta["modifiedTime"], meta["name"]


def read_gdoc(document_id, credentials_file):
    """Stessa firma e stessa uscita di read_docx: una lista di Block."""
    docs, _ = _google_services(credentials_file)
    doc = docs.documents().get(documentId=document_id).execute()

    blocks = []
    for i, el in enumerate(doc.get("body", {}).get("content", [])):
        para = el.get("paragraph")
        if not para:
            continue

        pieces, images, emphasis = [], [], False
        for e in para.get("elements", []):
            if "inlineObjectElement" in e:
                # L'id dell'oggetto e' stabile nel documento; contentUri no,
                # e' una URL temporanea. Come identita' usiamo l'id.
                images.append(e["inlineObjectElement"]["inlineObjectId"])
                continue
            tr = e.get("textRun")
            if not tr:
                continue
            t, style = tr.get("content", ""), tr.get("textStyle", {})
            if not t.strip():
                pieces.append(t)
                continue
            pre, core, post = _scomponi(t)
            if style.get("bold"):
                t, emphasis = f"{pre}**{core}**{post}", True
            elif style.get("italic"):
                t, emphasis = f"{pre}*{core}*{post}", True
            pieces.append(t)

        text = re.sub(r"[ \t]+", " ", "".join(pieces)).strip()
        plain = re.sub(r"[*_]+", "", text).strip()
        if not plain and not images:
            continue

        style_name = para.get("paragraphStyle", {}).get("namedStyleType", "")
        b = Block(
            idx=i,
            text=text,
            plain=plain,
            images=images,
            is_heading=style_name.startswith("HEADING"),
            has_emphasis=emphasis,
        )
        b.compute_hash()
        blocks.append(b)

    return blocks


# --- pre-classificazione euristica -----------------------------------------

DATE = re.compile(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\.?$")
ONLY_SYMBOLS = re.compile(r"^[\W\d_]+$", re.UNICODE)

# Non filtra e non cancella: alza solo una bandierina perche' la voce
# resti in attesa di una tua approvazione prima di finire sul link pubblico.
SENSITIVE_HINTS = {
    "suicide", "kill oneself", "kill themselves", "hang themself",
    "hang themselves", "take their own life", "commit suicide",
}

# Le euristiche possono buttare via simboli e date, MAI frasi: il giudizio su
# cosa sia chiacchiera spetta al modello, che vede il contesto. La prova sul
# campo: "One at a time" e "Got it!" erano finiti qui dentro, e sono voci vere.
LONG_BLOCK_WORDS = 40      # sopra questa soglia e' un testo, non una voce
SHORT_PLAIN_CHARS = 3


def pre_classify(block):
    p = block.plain
    low = p.lower().strip(" .!?:")
    words = len(p.split())

    if block.images:
        # Un blocco che porta un'immagine non si scarta mai per il suo testo:
        # il contenuto sta nella figura. Vale anche quando il testo e' "<".
        block.kind = "immagine" if not p else "da_classificare"
    elif DATE.match(p):
        block.kind = "marcatore_data"
    elif ONLY_SYMBOLS.match(p) or len(p) < SHORT_PLAIN_CHARS:
        block.kind = "scarto"
    elif words > LONG_BLOCK_WORDS:
        block.kind = "lettura"
    else:
        block.kind = "da_classificare"

    if block.images and block.kind != "immagine":
        block.flags.append("contiene_immagine")
    if any(h in low for h in SENSITIVE_HINTS):
        block.flags.append("sensibile")

    return block


def prepare(source, credentials_file=None):
    """source: un percorso .docx oppure un id di documento Google."""
    if source.lower().endswith(".docx"):
        raw = read_docx(source)
    else:
        raw = read_gdoc(source, credentials_file)
    return [pre_classify(b) for b in raw]


if __name__ == "__main__":
    import json
    import sys
    from collections import Counter

    src = sys.argv[1]
    blocks = prepare(src)

    print(f"blocchi totali: {len(blocks)}")
    for kind, n in Counter(b.kind for b in blocks).most_common():
        print(f"  {kind:>18}: {n}")

    flagged = [b for b in blocks if b.flags]
    print(f"  {'con bandierina':>18}: {len(flagged)}")

    dupes = len(blocks) - len({b.hash for b in blocks})
    print(f"  {'blocchi identici':>18}: {dupes}")

    with open("blocks.json", "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in blocks], f, ensure_ascii=False, indent=1)
