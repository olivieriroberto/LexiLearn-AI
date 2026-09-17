# Prompt di estrazione

Ricevi una finestra di blocchi consecutivi presi dagli appunti di una lezione
di inglese, numerati. Gli appunti sono scritti in diretta durante la lezione:
sono frammentari, pieni di refusi e non sempre corretti.

Restituisci **solo** un array JSON, senza testo attorno e senza backtick.

## Regola fondamentale

Il significato quasi mai sta dentro un solo blocco. "TO DIE -" e' completato
dal blocco successivo, "Noise" e "nose" hanno senso solo insieme, una regola
di grammatica e' sparsa su cinque righe. **Ragiona sul gruppo, non sulla riga.**
Ogni voce che produci elenca in `blocchi` tutti gli indici da cui proviene.

I blocchi in testa e in coda alla finestra potrebbero appartenere a un gruppo
tagliato a meta': se un gruppo sembra incompleto al bordo, mettilo con
`confidenza` bassa e segnalalo in `note`.

## Segnali della prof

- **Grassetto e corsivo**: marcano cio' che conta. Alzano la confidenza.
- **MAIUSCOLO dentro una frase minuscola**: marca l'elemento insegnato.
  "It depends ON the results" insegna la preposizione, non la frase.
  In questi casi il tipo e' quasi sempre `collocazione`.
- **Trattino**: separa il termine dalla spiegazione della prof. Spesso
  la parte dopo il trattino manca: completala tu.
- **Slash**: elenca alternative o sinonimi ("fix / resolve / solve").

## Testi lunghi

Un blocco marcato `[TESTO LUNGO]` e' un articolo che la prof ha incollato
per farlo leggere. **Non e' materiale da vocabolario e non va smontato in
voci.** Blocchi lunghi consecutivi appartengono allo stesso articolo:
raccoglili in **una sola** voce di tipo `lettura`, con `titolo`, l'elenco di
tutti i suoi blocchi, e in `espressioni_evidenziate` le sole espressioni che
la prof ha marcato in grassetto o corsivo dentro il testo.

Dal corpo dell'articolo non estrarre altro. Il lessico specialistico che
compare li' dentro (termini medici, nomi propri, tecnicismi) non e' lingua
da studiare: lascialo stare. Le parole che la prof ha invece ripreso su
righe corte proprie, fuori dall'articolo, quelle si' diventano voci normali.

Le consegne dell'esercizio ("Skim through the paragraph", "Does it apply to
you?") appartengono alla lettura, non sono voci di dizionario.

## Tipi ammessi

| tipo | quando |
|---|---|
| `termine` | parola singola con un significato |
| `espressione` | locuzione o frase idiomatica |
| `phrasal_verb` | verbo + particella |
| `collocazione` | quale preposizione o struttura regge una parola |
| `coppia` | due o piu' elementi che hanno senso solo a confronto: confondibili per suono o grafia, sinonimi con sfumature diverse, varianti britannico/americano |
| `regola` | una regola di grammatica o d'uso |
| `scarto` | chiacchiera, frammento senza contenuto, residuo di battitura |

## Traduzioni

La traduzione della prof va **conservata sempre** in `traduzione_prof`,
testuale, anche quando e' sbagliata o e' un frammento fuori posto.
In `traduzione` scrivi la tua, corretta e completa.

Se le due divergono in modo sostanziale, aggiungi `"divergenza": true` e
spiega in `note`. Non correggere silenziosamente e non cancellare mai la
versione della prof: il contesto della lezione vale piu' della precisione.

## Refusi

Il lemma va normalizzato ("well preseverd" -> "well preserved"), ma la forma
originale resta in `forma_prof` e il fatto va scritto in `note`.
Se il refuso rende il blocco ambiguo, confidenza sotto 0.6.

## Contenuti sensibili

Se un gruppo di blocchi tratta autolesionismo, morte violenta, sesso o altri
temi che non pubblicheresti senza pensarci, metti `"stato": "in_attesa"` su
**tutte** le voci del gruppo, non solo su quella che contiene la parola.
Estrai comunque cio' che e' puramente linguistico e lascia fuori i dettagli
concreti. Non decidi tu se pubblicare: decide una persona.

## Economia dei campi

Lo schema e' pensato per la parola singola. Applicato tale e quale a una
frase produce voci gonfie e ripetitive. Quattro regole:

1. **Un campo che non hai, lo ometti.** Mai `null`, mai stringhe vuote.
2. **IPA solo dove serve**: voci di una o due parole, oppure coppie in cui
   la pronuncia e' il punto. Su una frase, al massimo la trascrizione della
   sola parola difficile. Mai su una frase intera.
3. **Gli esempi devono aggiungere qualcosa.** Se l'esempio coincide con il
   lemma, non e' un esempio: ometti il campo.
4. **`traduzione` solo se corregge o completa `traduzione_prof`.** Se dicono
   la stessa cosa, tieni quella della prof e basta.

## Direzione

Non tutte le voci vanno dall'inglese all'italiano. Quando la prof risponde a
una domanda posta in italiano ("sono in 4 - there are 4 of them"), la parte
italiana e' lo spunto, non la traduzione dell'inglese. Segnalalo con
`"direzione": "it>en"`; negli altri casi `"en>it"`.

## Tre errori da non fare

**Il lemma e' sempre in inglese**, anche quando la voce nasce da una
domanda posta in italiano. Se la prof ha scritto "Riesco a preparare" e poi
la resa inglese, il lemma e' `to manage to`, non la frase italiana: quella
va in `forma_prof`. Un lemma italiano rende la voce introvabile.

**Il lemma e' la forma da dizionario**, non la frase in cui compare.
`bucket list`, non `at the top of one's bucket list`. Niente possessivi,
niente soggetti, niente contesto: quello va negli esempi.

**Non emettere il termine da solo E la coppia che lo contiene.** Se stai
facendo una `coppia` con noise e nose, non aggiungere anche una voce
`termine` per noise. Fai l'una o l'altra. Una voce a parte si giustifica
solo se quella parola ha un significato ulteriore che la coppia non copre.

**Una riga breve con un'espressione autonoma merita la sua voce anche se hai
gia' citato quel blocco altrove.** Righe come "so far", "As I've said",
"JUST FYI", "One at a time" sono voci a pieno titolo: non lasciarle dentro
l'esempio di un'altra voce. Citare un blocco non significa averlo estratto.

## Confine delle letture

Una `lettura` contiene **solo** i blocchi marcati `[TESTO LUNGO]` che le
appartengono, piu' l'eventuale titolo e le consegne dell'esercizio. Le righe
brevi di vocabolario che stanno prima o dopo l'articolo **non** vanno dentro
la lettura: sono voci normali.

Se l'articolo sembra cominciare prima o continuare dopo i blocchi che vedi,
dillo in `note`: le finestre tagliano i testi lunghi a meta' e i pezzi
verranno riuniti dopo.

## Schema

```json
{
  "tipo": "termine",
  "direzione": "en>it",
  "lemma": "forma canonica minuscola, chiave di deduplicazione",
  "forma_prof": "come appare negli appunti",
  "traduzione_prof": "solo se la prof l'ha scritta",
  "traduzione": "la tua",
  "definizione": "una riga, in italiano",
  "ipa": "britannica, solo se la voce e' breve",
  "esempi": ["presi dagli appunti quando ci sono"],
  "variante": "BrE | AmE, solo se rilevante",
  "blocchi": [3, 4],
  "confidenza": 0.0,
  "stato": "pubblicata | in_attesa",
  "note": "solo se c'e' qualcosa da dire"
}
```

Per `coppia` sostituisci `lemma` con `elementi` (array di lemmi) e aggiungi
`differenza`. Per `regola` usa `titolo`, `spiegazione`, `esempi`.
Per `scarto` bastano `blocchi` e `note`.
