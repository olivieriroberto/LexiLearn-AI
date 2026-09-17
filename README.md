[README.md](https://github.com/user-attachments/files/32340217/README.md)
# Dizionario di inglese — catena di estrazione

Legge gli appunti della lezione, ne ricava voci strutturate e le fonde con
quelle gia' presenti. Tre passi separati, ognuno eseguibile da solo.

```
prep.py       documento  ->  blocchi (con hash, formattazione, immagini)
extract.py    blocchi    ->  voci grezze (chiamate al modello)
merge.py      voci       ->  dizionario.json (ripulito e deduplicato)
normalize.py  lemmi      ->  fusioni proposte, applicate dopo revisione
sito.py       dizionario ->  dizionario.html (pagina unica, offline)
```

## Installazione

```bash
pip install anthropic python-docx google-api-python-client google-auth
```

## Variabili d'ambiente

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_CREDENTIALS_FILE="/percorso/service-account.json"
export EXTRACT_MODEL="claude-sonnet-4-6"       # opzionale
```

## Preparare l'accesso al documento

1. Su Google Cloud: nuovo progetto, poi attiva **Google Docs API** e
   **Google Drive API**.
2. Crea un **account di servizio** e scarica la sua chiave in formato JSON.
   L'indirizzo dell'account e' dentro il file, nel campo `client_email`.
3. La prof apre il documento, clicca Condividi, incolla quell'indirizzo come
   **Visualizzatore** e toglie la spunta della notifica via email.
4. L'id del documento e' la parte lunga dell'URL fra `/d/` e `/edit`.

Se il dominio della prof blocca la condivisione esterna, l'account di
servizio viene rifiutato: in quel caso si passa a OAuth con il tuo account,
ricordando di pubblicare l'app, perche' in stato di test Google scade i
token ogni sette giorni.

## Uso

Sul file scaricato, senza toccare Google:

```bash
python3 prep.py appunti.docx        # statistiche e blocks.json
python3 extract.py appunti.docx     # -> voci_grezze.json
python3 merge.py voci_grezze.json   # -> dizionario.json
```

Sul documento vivo:

```bash
python3 extract.py 1AbC...XyZ       # l'id del documento
```

## Costi

Il documento di prova, 362 blocchi e circa 3.300 parole, produce una
ventina di chiamate contando la seconda passata. Qualche decina di
centesimi in tutto. La sincronizzazione periodica manda al modello **solo i
blocchi nuovi**, quindi a regime ogni lezione costa una frazione di questo.

## Parametri che conviene conoscere

| dove | cosa | perche' |
|---|---|---|
| `extract.py` | `FINESTRA = 25` | blocchi per chiamata |
| `extract.py` | `SOVRAPPOSIZIONE = 5` | evita di perdere i gruppi a cavallo del taglio |
| `prep.py` | `LONG_BLOCK_WORDS = 40` | sopra questa soglia il blocco e' un testo di lettura |
| `prep.py` | `SENSITIVE_HINTS` | rete di sicurezza, non il filtro principale |

## Banco di prova

`dizionario.json` contiene 131 voci estratte a mano dal documento di
esempio, con copertura del 100% dei blocchi. E' il riferimento contro cui
misurare l'output automatico: rilanciando la catena sullo stesso documento,
le differenze dicono quanto il prompt e' fedele.
