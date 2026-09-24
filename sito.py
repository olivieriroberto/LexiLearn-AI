"""
Passo 5: dal JSON a una pagina che si apre con un doppio clic.

  python sito.py dizionario.json        ->  dizionario.html

Se accanto c'e' blocks.json, il testo integrale degli articoli viene
ripreso da li' e messo dentro le letture, grassetto della prof compreso:
nel dizionario ci sono solo i numeri dei blocchi, non il testo.
"""

import html
import json
import os
import re
import sys
from datetime import datetime, timezone


def blocchi_in_html(testo):
    """Il testo di un blocco, con i marcatori della prof resi in HTML."""
    t = html.escape(testo)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


def arricchisci_letture(voci, percorso_blocchi):
    """Attacca a ogni lettura il testo dei suoi blocchi."""
    if not os.path.exists(percorso_blocchi):
        return 0
    blocchi = {b["idx"]: b for b in
               json.load(open(percorso_blocchi, encoding="utf-8"))}
    fatte = 0
    for v in voci:
        if v.get("tipo") != "lettura":
            continue
        righe = []
        for i in sorted(v.get("blocchi", [])):
            b = blocchi.get(i)
            if b and b.get("text"):
                righe.append(blocchi_in_html(b["text"]))
        if righe:
            v["testo"] = righe
            fatte += 1
    return fatte


TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dizionario di inglese</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
:root{
  --carta:#EEF1F6; --foglio:#FFFFFF; --inchiostro:#15263C; --tenue:#5C6B82;
  --riga:#D3DAE5; --penna:#B03A1F; --evidenza:#FDF3D7;
  --serif:"IBM Plex Serif",Georgia,"Times New Roman",serif;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
}
:root:not([data-theme="light"]){ color-scheme:light dark; }
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --carta:#0F1621; --foglio:#16202E; --inchiostro:#E4EAF2; --tenue:#93A2B8;
    --riga:#2A3648; --penna:#E8836A; --evidenza:#2A2718;
  }
}
*{box-sizing:border-box}
body{
  margin:0;background:var(--carta);color:var(--inchiostro);
  font-family:var(--sans);font-size:16px;line-height:1.55;
  -webkit-text-size-adjust:100%;
}
.guscio{max-width:60rem;margin:0 auto;padding:0 1.25rem 5rem}
header{padding:2.5rem 0 1.25rem}
h1{font-family:var(--serif);font-size:1.6rem;font-weight:600;margin:0 0 .15rem}
.sottotitolo{color:var(--tenue);font-size:.9rem;margin:0}

.vetrina{background:var(--foglio);border:1px solid var(--riga);border-radius:3px;
  padding:1.5rem 1.25rem;margin:1.25rem 0 1.75rem}
.vetrina .etichetta{color:var(--tenue);font-size:.82rem;margin:0 0 1rem}
.duello{display:grid;grid-template-columns:1fr 1px 1fr;gap:1.25rem;align-items:start}
.duello .barra{background:var(--riga);align-self:stretch}
.duello b{display:block;font-family:var(--serif);font-size:1.5rem;font-weight:600;line-height:1.2}
.duello span{color:var(--tenue);font-size:.9rem}
.vetrina p.diff{margin:1.1rem 0 0;font-size:.95rem}
@media (max-width:34rem){
  .duello{grid-template-columns:1fr;gap:.6rem}
  .duello .barra{height:1px}
}

.comandi{position:sticky;top:0;z-index:5;background:var(--carta);
  padding:.75rem 0;border-bottom:1px solid var(--riga);margin-bottom:1rem}
input[type=search]{width:100%;padding:.7rem .85rem;font:inherit;color:inherit;
  background:var(--foglio);border:1px solid var(--riga);border-radius:3px}
input[type=search]:focus-visible,button:focus-visible,summary:focus-visible{
  outline:2px solid var(--penna);outline-offset:2px}
.filtri{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem}
.filtri button{font:inherit;font-size:.85rem;padding:.3rem .7rem;cursor:pointer;
  background:none;color:var(--tenue);border:1px solid var(--riga);border-radius:2rem}
.filtri button.azione{margin-left:auto;border-color:var(--inchiostro);
  color:var(--inchiostro);font-weight:500}
.filtri button[aria-pressed=true]{background:var(--inchiostro);color:var(--carta);
  border-color:var(--inchiostro)}
.barraviste{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;
  color:var(--tenue);font-size:.85rem;margin:0 0 1rem}
.barraviste button{font:inherit;font-size:.85rem;background:none;border:0;
  color:var(--tenue);cursor:pointer;padding:.2rem 0;border-bottom:2px solid transparent}
.barraviste button[aria-pressed=true]{color:var(--inchiostro);
  border-bottom-color:var(--inchiostro);font-weight:500}
.barraviste .sep{width:1px;height:1rem;background:var(--riga)}

article{background:var(--foglio);border:1px solid var(--riga);border-radius:3px;
  padding:1.1rem 1.25rem;margin-bottom:.6rem}
article.coppia{border-left:3px solid var(--inchiostro)}
article.regola{background:var(--evidenza)}
.testa{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem .7rem}
.lemma{font-family:var(--serif);font-size:1.25rem;font-weight:600}
.ipa{font-family:var(--serif);font-style:italic;color:var(--tenue);font-size:.95rem}
.tipo{margin-left:auto;color:var(--tenue);font-size:.78rem}
.trad{margin:.35rem 0 0;font-size:1rem}
.def{margin:.5rem 0 0;color:var(--tenue);font-size:.93rem;max-width:62ch}
.esempi{margin:.7rem 0 0;padding:0;list-style:none}
.esempi li{font-family:var(--serif);font-size:.98rem;padding-left:.8rem;
  border-left:2px solid var(--riga);margin-bottom:.25rem}
.prof{margin:.7rem 0 0;font-size:.88rem;color:var(--tenue);
  padding-top:.6rem;border-top:1px dotted var(--riga)}
.segnale{color:var(--penna);font-size:.85rem;margin:.5rem 0 0}
button.suono{font:inherit;font-size:.85rem;cursor:pointer;background:none;
  border:1px solid var(--riga);border-radius:2px;color:var(--tenue);padding:.1rem .45rem}
.confronto{display:grid;grid-template-columns:1fr 1px 1fr;gap:1rem;margin-top:.2rem}
.confronto .barra{background:var(--riga)}
.confronto b{font-family:var(--serif);font-size:1.15rem;display:block}
@media (max-width:34rem){
  .confronto{grid-template-columns:1fr;gap:.4rem}
  .confronto .barra{height:1px}
}
.vuoto{color:var(--tenue);padding:2rem 0}

/* piede di pagina */
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--riga);
  color:var(--tenue);font-size:.85rem;display:flex;gap:.5rem 1.25rem;
  flex-wrap:wrap;align-items:baseline;justify-content:space-between}
footer a{color:var(--tenue);text-decoration:none;
  border:1px solid var(--riga);border-radius:2rem;padding:.35rem .9rem}
footer a:hover,footer a:focus-visible{color:var(--inchiostro);
  border-color:var(--inchiostro)}
footer .vecchio{color:var(--penna)}

/* elenco compatto */
.lettera{font-family:var(--serif);font-size:1.1rem;font-weight:600;
  color:var(--tenue);margin:1.5rem 0 .3rem;padding-bottom:.2rem;
  border-bottom:1px solid var(--riga)}
details.voce{background:var(--foglio);border:1px solid var(--riga);
  border-radius:3px;margin-bottom:.3rem}
details.voce summary{cursor:pointer;padding:.55rem .85rem;display:flex;
  gap:.75rem;align-items:baseline;list-style:none}
details.voce summary::-webkit-details-marker{display:none}
details.voce summary .v{font-family:var(--serif);font-weight:600;flex:0 0 auto}
details.voce summary .t{color:var(--tenue);font-size:.9rem;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
details.voce summary .r{margin-left:auto;color:var(--penna);font-size:.8rem;flex:0 0 auto}
details.voce article{border:0;margin:0;padding-top:0}

/* letture */
details.lettura{background:var(--foglio);border:1px solid var(--riga);
  border-radius:3px;margin-bottom:.6rem;padding:0 1.25rem}
details.lettura summary{cursor:pointer;padding:1.1rem 0;font-family:var(--serif);
  font-size:1.25rem;font-weight:600}
.brano{font-family:var(--serif);max-width:66ch;padding-bottom:1.25rem}
.brano p{margin:0 0 .8rem;line-height:1.7}
.brano strong{background:var(--evidenza);font-weight:600;padding:0 .12em}

/* approvazione */
.pannello{background:var(--foglio);border:1px solid var(--penna);
  border-radius:3px;padding:.9rem 1.1rem;margin-bottom:1rem;font-size:.9rem}
.pannello button{font:inherit;font-size:.85rem;margin-top:.6rem;
  padding:.35rem .8rem;cursor:pointer;background:none;color:inherit;
  border:1px solid var(--riga);border-radius:3px}
.decidi{display:flex;gap:.4rem;margin-top:.8rem;padding-top:.7rem;
  border-top:1px dotted var(--riga)}
.decidi button{font:inherit;font-size:.85rem;padding:.3rem .8rem;cursor:pointer;
  background:none;color:var(--tenue);border:1px solid var(--riga);border-radius:3px}
.decidi button[aria-pressed=true]{background:var(--inchiostro);color:var(--carta);
  border-color:var(--inchiostro)}

#ripasso{position:fixed;inset:0;background:var(--carta);z-index:10;
  display:none;padding:1.25rem;overflow:auto}
#ripasso.aperto{display:block}
.carta{max-width:34rem;margin:8vh auto 0;background:var(--foglio);
  border:1px solid var(--riga);border-radius:3px;padding:2rem 1.5rem;text-align:center}
.carta .fronte{font-family:var(--serif);font-size:2rem;font-weight:600;line-height:1.2}
.carta .retro{margin-top:1.25rem;font-size:1.05rem}
.carta .retro small{display:block;color:var(--tenue);margin-top:.5rem;font-size:.9rem}
.azioni{display:flex;gap:.5rem;justify-content:center;margin-top:1.5rem;flex-wrap:wrap}
.azioni button,.chiudi{font:inherit;padding:.55rem 1.1rem;cursor:pointer;
  border-radius:3px;border:1px solid var(--riga);background:var(--foglio);color:inherit}
.azioni button.sai{background:var(--inchiostro);color:var(--carta);border-color:var(--inchiostro)}
.chiudi{position:absolute;top:1.25rem;right:1.25rem}
.avanzamento{text-align:center;color:var(--tenue);font-size:.85rem;margin-top:1rem}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<div class="guscio">
<header>
  <h1>Dizionario di inglese</h1>
  <p class="sottotitolo" id="riassunto"></p>
</header>

<section class="vetrina" id="vetrina" hidden>
  <p class="etichetta">Due parole da non confondere</p>
  <div class="duello">
    <div><b id="v1"></b><span id="v1s"></span></div>
    <div class="barra"></div>
    <div><b id="v2"></b><span id="v2s"></span></div>
  </div>
  <p class="diff" id="vdiff"></p>
</section>

<div class="comandi">
  <input type="search" id="cerca" placeholder="Cerca una parola, una traduzione, un esempio" autocomplete="off">
  <div class="filtri" id="filtri"></div>
</div>

<div class="barraviste">
  <span>Vista</span>
  <button id="bElenco" aria-pressed="true">Elenco</button>
  <button id="bSchede" aria-pressed="false">Schede</button>
  <span class="sep"></span>
  <span>Ordine</span>
  <button id="bAlfa" aria-pressed="true">A-Z</button>
  <button id="bLezione" aria-pressed="false">Per lezione</button>
  <span class="sep"></span>
  <span id="conteggio"></span>
</div>

<main id="elenco"></main>

<footer>
  <span id="aggiornato"></span>
  <a id="lancia" href="#" hidden>Sincronizza ora</a>
</footer>
</div>

<div id="ripasso" role="dialog" aria-modal="true" aria-label="Ripasso">
  <button class="chiudi" onclick="chiudiRipasso()">Chiudi</button>
  <div class="carta">
    <div class="fronte" id="fronte"></div>
    <div class="retro" id="retro" hidden></div>
    <div class="azioni" id="azioni"></div>
  </div>
  <p class="avanzamento" id="avanzamento"></p>
</div>

<script>
const VOCI = __DATI__;
const GENERATO = "__GENERATO__";
const REPO = "__REPO__";

const nome = v => v.lemma || v.titolo || (v.elementi||[]).join(" / ")
  || (v.tipo === "gruppo_trattenuto" ? "Blocchi non estratti" : "");
const testo = v => [nome(v), v.traduzione, v.traduzione_prof, v.definizione,
                    v.differenza, v.spiegazione, (v.esempi||[]).join(" "),
                    v.forma_prof].filter(Boolean).join(" ").toLowerCase();
const ordinabile = v => nome(v).toLowerCase()
  .replace(/^(to|a|an|the)\s+/, "").replace(/[^a-z ]/g, "");
const primaLettera = v => (ordinabile(v)[0] || "#").toUpperCase();

let decisioni = {};
try{ decisioni = JSON.parse(localStorage.getItem("dizionario-decisioni")) || {}; }
catch(e){}

const pubbliche = () => VOCI.filter(v =>
  v.stato !== "in_attesa" || decisioni[nome(v)] === "approvata");
const inAttesa = () => VOCI.filter(v =>
  v.stato === "in_attesa" && decisioni[nome(v)] !== "approvata");
const coppie = VOCI.filter(v => v.tipo === "coppia" && v.differenza
  && v.stato !== "in_attesa");

function parla(t){
  if(!window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(t);
  u.lang = "en-GB"; speechSynthesis.cancel(); speechSynthesis.speak(u);
}

/* ---------- vetrina ---------- */
if(coppie.length){
  const c = coppie[Math.floor(Date.now()/864e5) % coppie.length];
  const [a,b] = c.elementi, parti = (c.traduzione||"").split("/");
  v1.textContent = a; v2.textContent = b || "";
  v1s.textContent = (parti[0]||"").trim();
  v2s.textContent = (parti[1]||"").trim();
  vdiff.textContent = c.differenza;
  vetrina.hidden = false;
}

/* ---------- comandi ---------- */
const TIPI = [["", "Tutto"], ["coppia","Coppie"], ["regola","Regole"],
              ["espressione","Espressioni"], ["termine","Parole"],
              ["phrasal_verb","Phrasal verb"], ["collocazione","Collocazioni"],
              ["lettura","Letture"], ["in_attesa","Da approvare"]];
let filtro = "", vista = "elenco", ordine = "alfa";

filtri.innerHTML = TIPI.map(([k,e]) =>
  `<button data-k="${k}" aria-pressed="${k===""}">${e}</button>`).join("")
  + `<button data-k="ripasso" class="azione">Ripassa</button>`;

filtri.addEventListener("click", e => {
  const b = e.target.closest("button"); if(!b) return;
  if(b.dataset.k === "ripasso") return apriRipasso();
  filtro = b.dataset.k;
  [...filtri.children].forEach(x =>
    x.dataset.k !== "ripasso" && x.setAttribute("aria-pressed", x.dataset.k === filtro));
  disegna();
});
cerca.addEventListener("input", disegna);

function coppiaDiBottoni(a, b, valA, valB, quale){
  a.setAttribute("aria-pressed", quale === valA);
  b.setAttribute("aria-pressed", quale === valB);
}
bElenco.onclick = () => { vista = "elenco"; disegna(); };
bSchede.onclick = () => { vista = "schede"; disegna(); };
bAlfa.onclick   = () => { ordine = "alfa"; disegna(); };
bLezione.onclick= () => { ordine = "lezione"; disegna(); };

/* ---------- schede ---------- */
function corpo(v){
  let dentro = "";
  if(v.tipo === "coppia"){
    const el = v.elementi || [], lato = t =>
      `<b>${t}</b><button class="suono" data-dire="${t}">ascolta</button>`;
    dentro = `<div class="confronto">
        <div>${lato(el[0]||"")}</div><div class="barra"></div>
        <div>${el[1] ? lato(el[1]) : ""}</div></div>
      ${el.length > 2 ? `<p class="def">Anche: ${el.slice(2).join(", ")}</p>` : ""}
      ${v.ipa ? `<p class="ipa">${v.ipa}</p>` : ""}
      ${v.traduzione ? `<p class="trad">${v.traduzione}</p>` : ""}
      <p class="def">${v.differenza || ""}</p>`;
  } else if(v.tipo === "gruppo_trattenuto"){
    dentro = `<div class="testa"><span class="lemma">Blocchi non estratti</span>
      <span class="tipo">gruppo trattenuto</span></div>`;
  } else if(v.tipo === "regola"){
    dentro = `<div class="testa"><span class="lemma">${v.titolo||""}</span></div>
      <p class="def">${v.spiegazione||""}</p>`;
  } else {
    dentro = `<div class="testa">
        <span class="lemma">${nome(v)}</span>
        ${v.ipa ? `<span class="ipa">${v.ipa}</span>` : ""}
        <button class="suono" data-dire="${nome(v)}">ascolta</button>
        <span class="tipo">${(v.tipo||"").replace("_"," ")}</span></div>
      ${v.traduzione ? `<p class="trad">${v.traduzione}</p>` : ""}
      ${v.definizione ? `<p class="def">${v.definizione}</p>` : ""}`;
  }

  const esempi = (v.esempi||[]).length
    ? `<ul class="esempi">${v.esempi.map(e=>`<li>${e}</li>`).join("")}</ul>` : "";
  const prof = v.forma_prof ? `<p class="prof">Negli appunti: ${v.forma_prof}</p>` : "";

  const seg = [];
  if(v.divergenza) seg.push("la traduzione della prof non corrisponde");
  if(v.confidenza != null && v.confidenza < 0.7) seg.push("ricostruita, da verificare");
  if(v.note) seg.push(v.note);
  const segnale = seg.length ? `<p class="segnale">${seg.join(" · ")}</p>` : "";

  const decidi = v.stato === "in_attesa" ? bottoniDecisione(v) : "";
  return dentro + esempi + prof + segnale + decidi;
}

function bottoniDecisione(v){
  const d = decisioni[nome(v)] || "";
  return `<div class="decidi" data-voce="${nome(v).replace(/"/g,"&quot;")}">
    <button data-d="approvata" aria-pressed="${d==="approvata"}">Pubblica</button>
    <button data-d="esclusa" aria-pressed="${d==="esclusa"}">Escludi</button>
  </div>`;
}

const scheda = v => `<article class="${v.tipo === "coppia" ? "coppia"
  : v.tipo === "regola" ? "regola" : ""}">${corpo(v)}</article>`;

function lettura(v){
  const brano = (v.testo||[]).length
    ? `<div class="brano">${v.testo.map(p=>`<p>${p}</p>`).join("")}</div>`
    : `<p class="def">Testo non disponibile: rigenera la pagina con blocks.json accanto.</p>`;
  const evid = (v.espressioni_evidenziate||[]).length
    ? `<p class="def">Espressioni segnate dalla prof: ${v.espressioni_evidenziate.join(" · ")}</p>`
    : "";
  return `<details class="lettura"><summary>${v.titolo||"Lettura"}</summary>
    ${evid}${brano}</details>`;
}

function riga(v){
  const trad = v.traduzione || v.traduzione_prof || v.differenza || v.spiegazione || "";
  const rosso = v.divergenza || (v.confidenza != null && v.confidenza < 0.7)
    ? "da verificare" : "";
  return `<details class="voce"><summary>
      <span class="v">${nome(v)}</span>
      <span class="t">${trad}</span>
      ${rosso ? `<span class="r">${rosso}</span>` : ""}
    </summary>${scheda(v)}</details>`;
}

/* ---------- disegno ---------- */
function disegna(){
  coppiaDiBottoni(bElenco, bSchede, "elenco", "schede", vista);
  coppiaDiBottoni(bAlfa, bLezione, "alfa", "lezione", ordine);

  const q = cerca.value.trim().toLowerCase();
  const attesa = filtro === "in_attesa";
  let lista = attesa ? inAttesa()
    : pubbliche().filter(v => !filtro || v.tipo === filtro);
  if(q) lista = lista.filter(v => testo(v).includes(q));

  lista = [...lista].sort((a,b) => ordine === "alfa"
    ? ordinabile(a).localeCompare(ordinabile(b))
    : Math.min(...(a.blocchi||[999])) - Math.min(...(b.blocchi||[999])));

  conteggio.textContent = `${lista.length} voci`;

  if(!lista.length){
    elenco.innerHTML = `<p class="vuoto">Nessuna voce per «${cerca.value}».
      Prova con la traduzione italiana.</p>`;
    return;
  }

  const intestazione = attesa ? `<div class="pannello">
      Queste voci sono state trattenute dall'estrazione: contengono lessico
      delicato, oppure sono ricostruzioni troppo incerte. Decidi tu.
      Le decisioni restano su questo dispositivo finche' non c'e' un archivio
      condiviso: scaricale se vuoi conservarle.
      <br><button onclick="scaricaDecisioni()">Scarica le decisioni</button>
    </div>` : "";

  let corpoHtml = "";
  if(filtro === "lettura"){
    corpoHtml = lista.map(lettura).join("");
  } else if(vista === "schede"){
    corpoHtml = lista.map(v => v.tipo === "lettura" ? lettura(v) : scheda(v)).join("");
  } else {
    let lettera = "";
    for(const v of lista){
      if(v.tipo === "lettura"){ corpoHtml += lettura(v); continue; }
      if(ordine === "alfa" && primaLettera(v) !== lettera){
        lettera = primaLettera(v);
        corpoHtml += `<p class="lettera">${lettera}</p>`;
      }
      corpoHtml += riga(v);
    }
  }
  elenco.innerHTML = intestazione + corpoHtml;
}

elenco.addEventListener("click", e => {
  const s = e.target.closest("[data-dire]");
  if(s){ e.preventDefault(); return parla(s.dataset.dire); }

  const b = e.target.closest(".decidi button");
  if(b){
    const voce = b.closest(".decidi").dataset.voce;
    decisioni[voce] = decisioni[voce] === b.dataset.d ? "" : b.dataset.d;
    try{ localStorage.setItem("dizionario-decisioni", JSON.stringify(decisioni)); }
    catch(err){}
    disegna();
  }
});

function scaricaDecisioni(){
  const blob = new Blob([JSON.stringify(decisioni, null, 1)],
                        {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "decisioni.json";
  a.click();
}

/* ---------- piede di pagina ----------
   Quando e' stato rigenerato il dizionario, e come chiedere una
   sincronizzazione subito senza aspettare il timer. Un pulsante che lanci
   davvero il workflow richiederebbe un token dentro la pagina, che essendo
   pubblica lo regalerebbe a chiunque: si apre invece la pagina di GitHub,
   dove il pulsante c'e' gia' ed e' protetto dal login. */
(function(){
  if(GENERATO && !GENERATO.startsWith("__")){
    const d = new Date(GENERATO);
    const ore = (Date.now() - d) / 36e5;
    const quando = ore < 1 ? "meno di un'ora fa"
      : ore < 24 ? `${Math.round(ore)} ore fa`
      : `${Math.round(ore/24)} giorni fa`;
    aggiornato.textContent = "Aggiornato " + quando + ", il "
      + d.toLocaleString("it-IT", {day:"numeric", month:"long",
                                   hour:"2-digit", minute:"2-digit"});
    if(ore > 12) aggiornato.className = "vecchio";
  }
  if(REPO && !REPO.startsWith("__")){
    lancia.href = `https://github.com/${REPO}/actions/workflows/sync.yml`;
    lancia.hidden = false;
  }
})();

riassunto.textContent =
  `${pubbliche().length} voci dalle lezioni · ${coppie.length} coppie da non confondere`;
disegna();

/* ---------- ripasso ---------- */
const RIPASSABILI = ["termine","espressione","phrasal_verb","collocazione","coppia"];
let mazzo = [], indice = 0;

function memoria(){
  try{ return JSON.parse(localStorage.getItem("dizionario-ripasso")) || {}; }
  catch(e){ return {}; }
}
function ricorda(id, salto){
  try{
    const m = memoria();
    m[id] = { quando: Date.now() + salto*864e5, salto };
    localStorage.setItem("dizionario-ripasso", JSON.stringify(m));
  }catch(e){}
}
function apriRipasso(){
  const m = memoria(), ora = Date.now();
  mazzo = pubbliche().filter(v => RIPASSABILI.includes(v.tipo))
    .filter(v => !m[nome(v)] || m[nome(v)].quando <= ora)
    .sort(() => Math.random() - .5);
  indice = 0; ripasso.classList.add("aperto"); mostra();
}
function chiudiRipasso(){ ripasso.classList.remove("aperto"); }
function mostra(){
  if(indice >= mazzo.length){
    fronte.textContent = mazzo.length ? "Finito per oggi" : "Niente da ripassare adesso";
    retro.hidden = true; azioni.innerHTML = "";
    avanzamento.textContent = mazzo.length ? `${mazzo.length} voci ripassate`
      : "Le voci ripassate tornano dopo qualche giorno.";
    return;
  }
  const v = mazzo[indice];
  fronte.textContent = nome(v);
  retro.hidden = true;
  retro.innerHTML = `${v.traduzione || v.traduzione_prof || ""}
    <small>${v.differenza || v.definizione || ""}</small>`;
  azioni.innerHTML = `<button onclick="scopri()">Mostra</button>
    <button class="sai" data-dire="${nome(v).replace(/"/g,"&quot;")}">Ascolta</button>`;
  avanzamento.textContent = `${indice+1} di ${mazzo.length}`;
}
azioni.addEventListener("click", e => {
  const b = e.target.closest("[data-dire]");
  if(b) parla(b.dataset.dire);
});
function scopri(){
  retro.hidden = false;
  azioni.innerHTML = `<button onclick="voto(1)">Da rivedere</button>
    <button onclick="voto(3)">Quasi</button>
    <button class="sai" onclick="voto(7)">La so</button>`;
}
function voto(giorni){ ricorda(nome(mazzo[indice]), giorni); indice++; mostra(); }
document.addEventListener("keydown", e => {
  if(e.key === "Escape") chiudiRipasso();
  if(e.key === " " && ripasso.classList.contains("aperto")){
    e.preventDefault(); if(retro.hidden) scopri();
  }
});
</script>
</body>
</html>
"""


def genera(sorgente="dizionario.json", uscita="dizionario.html",
           blocchi="blocks.json"):
    voci = json.load(open(sorgente, encoding="utf-8"))
    letture = arricchisci_letture(voci, blocchi)
    dati = json.dumps(voci, ensure_ascii=False).replace("</", "<\\/")
    pagina = (TEMPLATE
              .replace("__DATI__", dati)
              .replace("__GENERATO__",
                       datetime.now(timezone.utc).isoformat(timespec="seconds"))
              # GITHUB_REPOSITORY lo imposta Actions. In locale resta vuoto e
              # il collegamento non compare: non avrebbe senso.
              .replace("__REPO__", os.environ.get("GITHUB_REPOSITORY", "")))
    open(uscita, "w", encoding="utf-8").write(pagina)

    print(f"{len(voci)} voci -> {uscita}  ({len(pagina)//1024} KB)")
    if letture:
        print(f"{letture} letture con il testo integrale preso da {blocchi}")
    else:
        print(f"nessun {blocchi} accanto: le letture restano senza testo")
    print("Aprilo con un doppio clic.")


if __name__ == "__main__":
    genera(sys.argv[1] if len(sys.argv) > 1 else "dizionario.json",
           sys.argv[2] if len(sys.argv) > 2 else "dizionario.html")
