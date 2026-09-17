"""
Leggere il JSON che torna dal modello.

Il modello risponde quasi sempre con il solo array richiesto, ma "quasi
sempre" non basta quando gira da solo ogni cinque minuti. Capita che
aggiunga una frase di cortesia, che chiuda dentro i backtick, che tronchi
la risposta al limite dei token o che lasci una virgola di troppo prima
della parentesi. Nessuno di questi casi deve far perdere una finestra
intera.
"""

import json
import re

DECODER = json.JSONDecoder()


def json_array(testo):
    """Il primo array JSON valido dentro il testo, o [] se non ce n'e'."""
    if not testo:
        return []

    testo = re.sub(r"```(?:json)?", "", testo).strip()

    inizio = testo.find("[")
    if inizio < 0:
        return []

    # raw_decode si ferma alla fine del primo valore valido: cosi' una
    # frase o un secondo array attaccati dopo non fanno fallire tutto.
    try:
        return DECODER.raw_decode(testo, inizio)[0]
    except json.JSONDecodeError:
        pass

    # Virgola di troppo prima di una chiusura.
    ripulito = re.sub(r",\s*([\]}])", r"\1", testo[inizio:])
    try:
        return DECODER.raw_decode(ripulito, 0)[0]
    except json.JSONDecodeError:
        pass

    # Ultima risorsa: risposta troncata a meta'. Si recuperano gli oggetti
    # completi uno per uno, meglio di niente.
    voci, profondita, partenza = [], 0, None
    for i, c in enumerate(ripulito):
        if c == "{":
            if profondita == 0:
                partenza = i
            profondita += 1
        elif c == "}" and profondita:
            profondita -= 1
            if profondita == 0:
                try:
                    voci.append(json.loads(ripulito[partenza:i + 1]))
                except json.JSONDecodeError:
                    pass
    return voci
