# Benchmark PeerMoA — 6 configurazioni

Confronto di **e2e latency** e **throughput** tra schema push e schema pull, in
deployment singolo nodo e distribuito, con le due politiche di coda del pull.

> **Regola non negoziabile:** tutti e sei i run devono girare sullo **stesso commit**.
> Un confronto tra run su codice diverso non misura l'architettura, misura la
> differenza di codice. Annotare l'hash sotto e verificarlo prima di ogni run.

**Commit di riferimento:** `6be0568` (`git rev-parse --short HEAD`)

---

## Le sei configurazioni

Il nome coincide con il prefisso della cartella di log generata da `main.py`,
quindi ogni run e' identificabile senza consultare appunti esterni.

| # | Nome | Schema | Deployment | Politica di coda | Cartella di log |
|---|------|--------|------------|------------------|-----------------|
| 1 | `PUSH-LOCAL` | push (layerApplication) | 1 macchina | — | `logs/LA-LOCAL_<ts>/` |
| 2 | `PUSH-DIST` | push (layerApplication) | 3 macchine | — | `logs/LA-DIST_<ts>/` |
| 3 | `PULL-LOCAL-HEAD` | pull | 1 macchina | `head` | `logs/PULL-LOCAL-HEAD_<ts>/` |
| 4 | `PULL-DIST-HEAD` | pull | 3 macchine | `head` | `logs/PULL-DIST-HEAD_<ts>/` |
| 5 | `PULL-LOCAL-TAIL` | pull | 1 macchina | `tail` | `logs/PULL-LOCAL-TAIL_<ts>/` |
| 6 | `PULL-DIST-TAIL` | pull | 3 macchine | `tail` | `logs/PULL-DIST-TAIL_<ts>/` |

Le configurazioni push non hanno suffisso di politica perche' non hanno una coda
di task condivisa: la politica di requeue e' un parametro del solo schema pull.

### Le due politiche

Entrambe agiscono su `QueueHeadService./requeue`, cioe' su dove viene reinserito
un task che ha ricevuto un'elaborazione ma non ha ancora completato il layer.

- **`head`** — reinserimento in testa (`appendleft`). Da' priorita' al lavoro in
  corso, cosi' un task chiude il proprio layer prima. In deployment distribuito il
  worker co-locato con `QueueHeadService` puo' ri-prelevare immediatamente cio' che
  ha appena requeued, affamando i worker remoti.
- **`tail`** — reinserimento in coda (`append`). Rompe quel ciclo auto-alimentato,
  al costo di piu' work in progress e quindi di una latenza e2e attesa piu' alta.

---

## Parametri da tenere fissi

Da verificare identici su tutti e sei i run, e da compilare una sola volta.

| Parametro | Valore | Dove si controlla |
|---|---|---|
| Modello | `qwen2.5:1.5b` | menu interattivo (voce "Select the model") |
| Topic MMLU | `college_computer_science` | menu interattivo (voce "Select the benchmark's topic") |
| Query totali | 100 | dimensione dello split `test` del topic |
| Elaborazioni per query | 9 | push: 3 layer x 3 agenti — pull: 3 layer x 3 elaborazioni |
| Sintesi per query | 3 | una per virtual layer |
| Chiamate LLM per query | push 15, pull 12 | **non e' parita'**: vedi nota sotto |
| `target_queue_size` | 25 | `pull_queueHeadService.py` |
| Consumer di sintesi | 5 | `num_synth_workers` in `pull_synthOutService.py` |
| Macchine (run DIST) | `.12` master, `.5`, `.11` | IP effettivi al momento del run |
| Finestra in volo (push) | 10 | sliding window di `HeadBenchmarkService` |

### Hardware del cluster (solo run DIST)

L'eterogeneita' del cluster e' un **parametro dichiarato** dell'esperimento, non un
difetto: e' cio' che permette di misurare se uno schema sa instradare attorno a un nodo
lento. Va quindi misurata e riportata, non subita.

Misura per macchina, una richiesta alla volta, stesso prompt e stesso seed:

```bash
curl -s http://127.0.0.1:11434/api/generate -d '{
  "model":"qwen2.5:1.5b",
  "prompt":"Explain how binary search works, in about 200 words.",
  "stream":false,
  "options":{"temperature":0.7,"seed":1}
}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"{d['eval_count']/(d['eval_duration']/1e9):.1f} tok/s\")"
```

| Macchina | Ruolo | Inference | `OLLAMA_NUM_PARALLEL` | tok/s | Tempo di servizio `t_s` (s) |
|---|---|---|---|---|---|
| `.12` | master | GPU | | | ~2.1 |
| `.5` | worker 2 | GPU | | | ~2.5 |
| `.11` | worker 3 | **CPU** | | | **14.3** |

I `t_s` in tabella sono **ricavati dal run**, non misurati col `curl`. Per `.12` e `.5` sono
le mediane per chiamata osservate in `LA-DIST_20260808_1712`: entrambe le macchine girano
al ~15% di utilizzo, quindi la coda e' trascurabile e la mediana approssima `t_s`. Per
`.11`, satura, la mediana osservata (54.6s) e' inutilizzabile e `t_s` e' ricavato dal
throughput: `5 chiamate / 0.01398 query/s / 100 = 14.3s`. Sostituire con la misura diretta
`curl` a sistema scarico quando disponibile.

> **Nota sulla composizione del cluster.** I run DIST girano su `.12` + `.5` + `.11`. Una
> quarta macchina (`.100`, GTX 750 Ti) era il worker 2 iniziale ma la sua GPU non e'
> utilizzabile — driver 595 non supporta Maxwell e Secure Boot rifiuta il modulo DKMS —
> quindi girava in CPU a `t_s` ~210s, con una proiezione di ~18h per run. E' stata
> sostituita con `.5` prima di qualunque run valido. Il run interrotto
> `LA-DIST_20260808_1216` e' l'unico che la contiene e **non entra in nessuna tabella**.

**`t_s` non e' la latenza che leggi nei log del run.** Quella include l'attesa in coda e
quindi dipende dal carico, non dalla macchina: nel run `LA-DIST_20260808_1712` il worker
`.11` mostra 54.6s di mediana, ma il suo tempo di servizio e' ~15s — il resto e'
concorrenza (~3.6 richieste simultanee). Nel run precedente la stessa macchina mostrava
16.6s solo perche' era affamata da un collo di bottiglia altrove. Misura `t_s` con il
`curl` qui sopra, **una richiesta alla volta e a sistema scarico**, oppure ricavalo dal
run come `n_chiamate_per_query / throughput`.

**Stima a priori del wall clock di un run DIST.** In push il piazzamento e' statico e
simmetrico: ogni macchina esegue 5 chiamate LLM per query (3 `MidNodeService`, uno per
layer, piu' le 2 di `OutputNodeService-L{i}`). Nessuna macchina puo' sostituirne un'altra,
quindi il pavimento e':

```
wall_clock >= 5 x n_query x max(t_s)
```

Ne segue il criterio: perche' `PUSH-DIST` batta `PUSH-LOCAL` (2345.5s) serve
`max(t_s) < 4.7s`, cioe' ogni macchina entro circa 2x dal master. Se il criterio non e'
soddisfatto, il degrado di push e' atteso e va discusso, non corretto.

Verifica su `LA-DIST_20260808_1712`, a run concluso: `t_s` del nodo piu' lento (`.11`)
14.3s, quindi `5 x 100 x 14.3 = 7150s`. Wall clock osservato: **7151.8s**. Il pavimento non
e' solo rispettato, e' esattamente il valore raggiunto: in push distribuito la macchina piu'
lenta non e' un fattore di degrado tra tanti, e' *l'unico* termine che conta. Master e `.5`
restano al ~15% di utilizzo per tutto il run. La stima e' predittiva, non descrittiva: si
puo' calcolare **prima** di lanciare un run DIST.

**Attenzione al modello e al topic:** fino al commit corrente le scelte del menu non
raggiungevano i servizi pull, che restavano sui default hardcoded. Verificare nel log
la riga `QueueHeadService: topic '<topic>' | requeue policy '<policy>'` prima di
considerare valido un run.

---

## Procedura per run

1. `git rev-parse --short HEAD` e confronto con il commit di riferimento.
2. Ollama attivo su ogni macchina coinvolta, stesso modello scaricato.
3. Nessun run precedente in esecuzione (`ray stop --force` se serve).
4. Avvio:
   - **LOCAL** — `./run.sh` (oppure `python main.py` con `PEERMOA_RUN_MODE` non impostato)
   - **DIST** — `master_fixed_start.sh` sul master, poi i due `worker_fixed_start.sh`
     (vedi `dist/dist_running_scripts/fixed_start/README_pull_multi_host.md`)
5. A fine run, annotare la cartella di log prodotta nelle tabelle sotto.

---

## Risultati

### Metriche principali

Fonte: riga `FINAL METRICS` e insieme delle righe `LIVE METRICS` in `simulation.log`.

La colonna **in-flight** e' calcolata con Little (`latenza media x throughput`) e non e'
opzionale: senza di essa le latenze E2E non sono confrontabili tra schemi, perche' i tre
run locali girano a livelli di concorrenza molto diversi pur avendo throughput quasi
identico. Vedi le note in fondo.

| Configurazione | Cartella di log | E2E media (s) | E2E mediana (s) | E2E p95 (s) | Throughput (msg/s) | In-flight (Little) | Wall clock (s) | Accuracy (%) |
|---|---|---|---|---|---|---|---|---|
| `PUSH-LOCAL` | `LA-LOCAL_20260807_1155` | 229.89 | 226.52 | 332.25 | 0.0426 | 9.8 | 2345.5 | 52.0 |
| `PUSH-DIST` | `LA-DIST_20260808_1712` | 692.85 | 692.98 | 904.49 | 0.0140 | 9.7 | 7151.8 | 47.0 |
| `PULL-LOCAL-HEAD` | `PULL-LOCAL-HEAD_20260807_1258` | 97.39 | 90.61 | 157.83 | 0.0450 | 4.4 | 2220.5 | 47.5 |
| `PULL-DIST-HEAD` | `PULL-DIST-HEAD_20260809_1120` | 56.54 | 47.52 | 105.97 | 0.0767 | 4.3 | 1304.3 | 50.0 |
| `PULL-LOCAL-TAIL` | `PULL-LOCAL-TAIL_20260807_1349` | 592.01 | 608.05 | 710.36 | 0.0402 | 23.8 | 2485.9 | 50.5 |
| `PULL-DIST-TAIL` | `PULL-DIST-TAIL_20260809_1203` | 392.02 | 357.00 | 565.37 | 0.0665 | 26.1 | 1504.2 | 55.0 |

Il throughput e' ricalcolato come `query completate / wall clock`, non letto dal log (che
lo arrotonda a 2 decimali e collassa tutto su `0.04`). Il wall clock e' la differenza tra
la prima riga di `simulation.log` e la riga `FINAL METRICS`, quindi include il caricamento
del dataset: sottostima leggermente il throughput, in modo uniforme su tutti i run.

### Distribuzione del carico

Il punto critico: quanto lavoro e' stato davvero eseguito fuori dal master. Senza
questa colonna un guadagno di throughput non e' attribuibile alla distribuzione.

| Configurazione | Elab. nodo 1 | Elab. nodo 2 | Elab. nodo 3 | % sul nodo piu' carico | Chiamate LLM totali sul master |
|---|---|---|---|---|---|
| `PUSH-LOCAL` | 900 | — | — | 100% | 1500 |
| `PUSH-DIST` | 300 | 300 | 300 | 33.3% | 500 |
| `PULL-LOCAL-HEAD` | 294 | 302 | 304 | 100% (1 macchina) | 1200 |
| `PULL-DIST-HEAD` | **399** (`.12`) | **441** (`.5`) | **60** (`.11`) | **49.0%** | 699 |
| `PULL-LOCAL-TAIL` | 305 | 278 | 317 | 100% (1 macchina) | 1200 |
| `PULL-DIST-TAIL` | **328** (`.12`) | **511** (`.5`) | **61** (`.11`) | **56.8%** | 628 |

**Le due righe push non sono misurate, sono determinate per costruzione**, ed e' esattamente
il punto: il piazzamento e' statico (`dist_fixed_configs/machine_{a,b,c}_*.json`), quindi
ogni macchina esegue 3 elaborazioni `MidNodeService` per query — 300 su 100 query — piu' le
2 chiamate di `OutputNodeService-L{i}`, per 500 chiamate LLM a macchina. **Push non puo'
sbilanciarsi e non puo' ribilanciarsi**: la ripartizione 33.3/33.3/33.3 e' insensibile alla
velocita' delle macchine. Un cluster eterogeneo produce quindi un bilanciamento del *lavoro*
perfetto e un bilanciamento del *tempo* pessimo (`.11` al 100% di utilizzo, le altre due al
~15%). Questa e' la riga di controllo con cui confrontare le righe pull, dove la ripartizione
e' invece emergente e ci si aspetta che segua la capacita' dei nodi.

Per i run distribuiti il conteggio per nodo si legge dal log del driver, dove le
righe portano il prefisso dell'attore e l'IP:

```bash
grep "Processed Task ID" benchmark_output.log \
  | grep -oP "ElabMidNode-\d+ pid=\d+(, ip=[\d.]+)?" | sort | uniq -c
```

Per i run locali le righe non hanno prefisso di nodo, quindi si conta per servizio:

```bash
grep "Received Task ID" logs/<cartella>/simulation.log \
  | grep -oP "ElabMidService-\d+" | sort | uniq -c
```

**Il confronto che porta il risultato e' `PUSH-DIST` contro `PULL-DIST-HEAD`**: stesso
cluster fisico, stesse tre macchine, stesso commit, stesso topic. Cambia solo la disciplina
di assegnazione, e il carico si ripartisce in modo opposto:

| | `.12` master | `.5` | `.11` (CPU) | Throughput |
|---|---:|---:|---:|---:|
| `PUSH-DIST` (statico) | 300 (33.3%) | 300 (33.3%) | 300 (33.3%) | 0.0140 msg/s |
| `PULL-DIST-HEAD` (a domanda) | 399 (44.3%) | 441 (49.0%) | **60 (6.7%)** | **0.0767 msg/s** |

Il nodo lento passa da 300 elaborazioni imposte a 60 richieste: pull gliene assegna
esattamente quante ne sa smaltire, perche' e' il worker a chiedere quando e' libero. La
ripartizione osservata segue la capacita' delle macchine (`1/t_s` normalizzato darebbe
50 / 42 / 7%), con il master leggermente sotto perche' ospita anche le 300 sintesi di
`SynthOutService`. Il risultato e' **5.48x di throughput a parita' di hardware**.

Il modo pulito di dirlo e' che i due schemi hanno un tetto teorico diverso, e ciascuno lo
raggiunge quasi esattamente:

```
tetto push = 1 / (5 x max(t_s))       = 1 / (5 x 14.3)   = 0.0140 msg/s   -> osservato 0.0140 (100%)
tetto pull = (somma di 1/t_s_i) / 12  = 0.946 / 12       = 0.0788 msg/s   -> osservato 0.0767 (97%)
```

Nessuno dei due schemi e' implementato male: push gira al 100% del proprio tetto. La
differenza e' che **il tetto di push scala col nodo piu' lento, quello di pull con la somma
dei nodi**. Su un cluster omogeneo i due coincidono; su un cluster eterogeneo divergono di un
fattore pari al rapporto tra media armonica e minimo delle capacita' — qui 5.6x previsto,
5.48x osservato.

### Guadagno atteso vs osservato

Il controllo che smaschera un guadagno solo apparente: se la riduzione del wall
clock coincide con la frazione di lavoro delocalizzata, il vantaggio non e'
architetturale, e' solo lavoro tolto alla macchina satura.

| Coppia confrontata | Lavoro delocalizzato (%) | Riduzione wall clock (%) | Delta throughput (%) | Attribuibile alla distribuzione? |
|---|---|---|---|---|
| `PUSH-LOCAL` → `PUSH-DIST` | 66.7 | **−204.9** (peggiora 3.05x) | **−67.2** | No: degrado, non guadagno |
| `PULL-LOCAL-HEAD` → `PULL-DIST-HEAD` | 55.7 | 41.3 | **+70.4** | Si', con riserva (vedi sotto) |
| `PULL-LOCAL-TAIL` → `PULL-DIST-TAIL` | | | | |

Lettura della riga push: due terzi del lavoro sono usciti dal master e il risultato e' un
throughput ridotto a un terzo. Il confronto delle latenze in questa coppia e' inoltre
**legittimo senza correzioni**, perche' gli in-flight coincidono (9.8 contro 9.7: la sliding
window da 10 e' satura in entrambi i run), quindi i rapporti su media, mediana e p95 —
3.01x, 3.06x, 2.72x — misurano davvero l'architettura e non due punti di lavoro diversi. La
coerenza tra questi rapporti e quello del wall clock (3.05x) e' la conferma che il sistema
e' in regime stazionario in entrambi i casi.

Il meccanismo e' aritmetico: sul solo master una query costa 15 chiamate a ~2.1s; distribuita,
`.11` ne riceve 5 a 14.3s. Aggiungere capacita' a un sistema push non aiuta se la capacita'
aggiunta non e' fungibile con quella satura, e in push non lo e' mai: il piazzamento e'
deciso a deploy-time e `OutputNodeService` attende comunque 3 risposte su 3. **Questo e' il
controfattuale che da' significato ai run pull**: stesso cluster fisico, stesse macchine,
stesso commit: se pull-dist fa meglio di 0.0140 msg/s, il merito e' dello schema.

Lettura della riga pull, e la riserva. Il 55.7% di lavoro delocalizzato produce una riduzione
del wall clock del 41.3%: **meno** di quanto darebbe il puro spostamento di lavoro fuori da
una macchina satura, non di piu'. Preso alla lettera, il test di questa tabella dice quindi
che il guadagno di `PULL-LOCAL-HEAD` → `PULL-DIST-HEAD` e' compatibile con il semplice
offload e non prova nulla di architetturale — e la spiegazione e' che il master resta
saturo anche in distribuito (0.536 chiamate/s in dist contro 0.540 in locale: identico) e si
tiene tutte le 300 sintesi, mentre `.11` contribuisce pochissimo.

Questa riserva non indebolisce il risultato, ne' sposta il confronto: **il test giusto e'
`PUSH-DIST` contro `PULL-DIST-HEAD`**, dove il lavoro delocalizzato e' per definizione lo
stesso (tre macchine, tutte usate) e l'unica variabile e' *come* viene assegnato. La
coppia locale→distribuito misura l'effetto di aggiungere macchine; la coppia
push-dist→pull-dist misura l'effetto dello schema. Solo la seconda e' una tesi.

### Effetto della politica di coda

| Coppia confrontata | Delta E2E media (%) | Delta throughput (%) | Delta squilibrio (punti %) |
|---|---|---|---|
| `PULL-LOCAL-HEAD` → `PULL-LOCAL-TAIL` | +507.9 | −10.7 | n/a (1 macchina) |
| `PULL-DIST-HEAD` → `PULL-DIST-TAIL` | +593.4 | −13.3 | **+7.8 (peggiora)** |

L'attesa era: `tail` peggiora la latenza e2e (piu' work in progress) e migliora il
bilanciamento. **La prima meta' e' confermata, la seconda e' smentita.** `tail` peggiora
entrambe le cose, e il perche' e' istruttivo.

*Sul bilanciamento.* Passando da `head` a `tail` il master scende da 399 a 328 elaborazioni
e `.5` sale da 441 a 511; `.11` resta fermo (60 → 61). Il meccanismo del ciclo
auto-alimentato descritto sopra e' quindi reale e vale circa 8 punti percentuali: con `head`
il worker co-locato con `QueueHeadService` ri-preleva davvero cio' che ha appena requeued.
Ma **non era quello a causare lo squilibrio**. Lo squilibrio e' dettato dalla capacita' delle
macchine, e rimuovere il vantaggio di co-locazione non redistribuisce verso il nodo lento:
sposta lavoro dal master a `.5`, che era gia' il nodo piu' carico. Da qui il segno positivo
in tabella. Ne segue che **"% sul nodo piu' carico" e' una metrica di squilibrio fuorviante
per il pull**, dove la ripartizione *deve* essere disuguale se le macchine sono disuguali:
il riferimento corretto e' la capacita' (`1/t_s` normalizzato: 50 / 42 / 7%), non la parita'.

*Sul throughput.* Il calo del 13.3% non e' dovuto a nodi che restano senza lavoro. In
entrambi i run `ElabMidService-1` sul master e' occupato per il 96-98% del wall clock, e gli
eventi `Queue is empty` sono 34 (head) e 104 (tail) ma **tutti concentrati negli ultimi 25-50
secondi**, cioe' durante lo svuotamento finale della coda: a regime nessun worker e' mai
affamato. Il master e' saturo in entrambe le politiche; con `tail` e' semplicemente **meno
efficiente a parita' di saturazione**. La firma nei log e' netta — durata media di
un'elaborazione sul master, disaggregata per numero di elaborazioni gia' subite dal task:

| Politica | count 0 | count 1 | count 2 (chiude il layer) |
|---|---:|---:|---:|
| `head` | 4.2s | 2.7s | 2.6s |
| `tail` | 3.5s | 2.7s | **7.3s** |

Tutta la differenza sta nella terza elaborazione, quella che chiude il virtual layer e
consegna il task a `SynthOutService`. Interpretazione: `tail` **sincronizza** l'avanzamento
dei task — i ~25 task in coda progrediscono in lockstep e arrivano a `count 2` a ondate —
quindi le elaborazioni che chiudono un layer collidono sistematicamente con le sintesi degli
altri task sullo stesso Ollama del master. `head` invece serializza: un task chiude il layer
e viene sintetizzato prima che arrivi il successivo. Coerente con la concorrenza media di
sintesi misurata, 0.70 (head) contro 0.84 (tail), e con il fatto che la **mediana** delle
elaborazioni non si muove (2.79s → 2.85s) mentre la media sale del 38%: non e' un
rallentamento uniforme, sono collisioni occasionali. Questa e' l'interpretazione piu'
coerente con i dati disponibili, non una misura diretta: servirebbe strumentare il tempo di
coda dentro Ollama per chiuderla.

---

## Note sulla lettura dei dati

- **La latenza E2E non e' confrontabile tra schemi senza gli in-flight.** I tre run
  locali lo dimostrano: throughput 0.0426 / 0.0450 / 0.0402 msg/s (dispersione ±6%,
  tutti saturano lo stesso Ollama sulla stessa macchina) ma latenza media 229.89 /
  97.39 / 592.01s, cioe' un fattore 6. La differenza e' interamente spiegata dagli
  in-flight: 9.8 / 4.4 / 23.8. Concludere "pull-head e' 2.4x meglio di push perche'
  97s contro 230s" significa confrontare due punti di lavoro della stessa macchina,
  non due architetture — e il rapporto resta privo di significato anche in percentuale.
- **Il WIP in pull non e' un parametro, e' una conseguenza della policy.** Con `head`
  i task chiudono il layer subito e il work-in-progress resta basso (4.4); con `tail`
  ogni requeue finisce dietro tutta la coda e il WIP tende a `target_queue_size` (23.8).
  Non e' quindi pareggiabile con push, che e' fissato a 10 dalla sliding window.
  Conseguenza operativa: **il throughput e' la metrica primaria** (e' un rate, a sistema
  saturo non dipende dalla concorrenza), la latenza si riporta sempre accanto agli
  in-flight.
- **Push e pull non fanno lo stesso numero di chiamate LLM per query.** Push ne fa 15
  (9 `MidNodeService` + 2 per ciascuno dei 3 `OutputNodeService`, che chiama sia
  `elab_into_char` sia `elab_into_string`); pull ne fa 12 (9 elaborazioni + 1 sintesi per
  virtual layer). Pull parte quindi avvantaggiato del 25% sul lavoro totale, e va detto
  esplicitamente: parte del divario in locale (0.0450 contro 0.0426 msg/s, +5.6%) e' questo,
  non lo scheduling. Normalizzando per chiamata il quadro si rovescia — push-local spinge
  0.639 chiamate/s attraverso il master contro 0.540 di pull-local-head, perche' gira a
  in-flight 9.8 contro 4.4. **Il vantaggio di pull non e' per-chiamata, e' di allocazione**,
  e infatti si manifesta solo in distribuito su cluster eterogeneo (5.48x), dove il fattore
  1.25 di chiamate in meno spiega una frazione trascurabile del divario.
- **Il throughput riportato e' arrotondato a 2 decimali** (`{:.2f}` in
  `pull_synthOutService.py`), quindi a questi ritmi tutto collassa su `0.03 msg/s`.
  Ricalcolarlo come `query completate / wall clock` invece di leggerlo dal log.
- **L'accuracy si legge da fonti diverse nei due schemi.** `TailBenchmarkService` (push)
  logga una riga `Layer N (Actual: X, Predicted: Y)` per ciascuno dei 3 layer, quindi
  300 coppie per run: il valore confrontabile e' quello del **layer 3**. Il pull ne
  logga una sola per query. Non mediare le tre righe di push, o si confronta la qualita'
  intermedia con quella finale.
- **L'accuracy non e' deterministica.** Il `seed=2` fissa il campionamento del
  dataset, non l'output del modello: le elaborazioni girano a `temperature 0.7`.
  Con 100 query lo scarto tipico e' di diversi punti percentuali; non trarre
  conclusioni sulla qualita' senza ripetizioni. Concretamente: `PUSH-LOCAL` 52.0% contro
  `PUSH-DIST` 47.0% e' uno scarto di 5 punti con errore standard ~5 punti
  (`sqrt(0.5 x 0.5 / 100)`), cioe' entro un sigma. Il deployment non cambia il calcolo
  eseguito, quindi la differenza **e' rumore per costruzione** e va riportata come tale.
  Nel run dist i tre layer danno 45 / 46 / 47%, coerenti tra loro.
- **Lo skew di clock tra macchine non falsa le metriche** ma rende inutile
  correlare i timestamp tra log di macchine diverse: `start_time` e chiusura sono
  entrambi marcati sul master (`pull_queueHeadService.py`, `pull_synthOutService.py`).

---

## Conclusioni

Quadro d'insieme, throughput in msg/s (metrica primaria):

| Schema | LOCAL (1 macchina) | DIST (3 macchine) | Effetto della distribuzione |
|---|---:|---:|---:|
| push | 0.0426 | 0.0140 | **−67.2%** |
| pull `head` | 0.0450 | **0.0767** | **+70.4%** |
| pull `tail` | 0.0402 | 0.0665 | +65.4% |

### 1. Push vs pull a parita' di deployment

**Su una sola macchina i due schemi sono equivalenti; su tre macchine eterogenee pull vale
5.48 volte push.** In locale il divario e' +5.6% (0.0450 contro 0.0426) ed e' interamente
spiegato dal fatto che pull esegue 12 chiamate LLM per query contro le 15 di push: a parita'
di chiamate, push e' anzi leggermente piu' efficiente perche' lavora a in-flight 9.8 contro
4.4 e spinge 0.639 chiamate/s attraverso il master contro 0.540. **Il vantaggio di pull non
e' per-chiamata, e' di allocazione**, e per definizione non puo' manifestarsi finche' c'e'
una sola macchina a cui allocare.

In distribuito il divario diventa 0.0767 contro 0.0140. La spiegazione non richiede ipotesi:
i due schemi hanno tetti teorici diversi e ciascuno raggiunge il proprio quasi esattamente
(push 100%, pull 97%). Il tetto di push e' `1/(k x max(t_s))` — scala col **nodo piu'
lento**; quello di pull e' `(somma di 1/t_s_i)/k` — scala con la **somma dei nodi**. Su
cluster omogeneo coincidono; su cluster eterogeneo divergono del rapporto tra media armonica
e minimo delle capacita'. Con `t_s` = 2.1 / 2.5 / 14.3s il rapporto previsto e' 5.6x, quello
osservato 5.48x.

Il punto teorico da portare in tesi e' che **la differenza non e' di efficienza ma di
fungibilita' della capacita'**. In push il piazzamento e' deciso a deploy-time e
`OutputNodeService` attende comunque 3 risposte su 3: la capacita' aggiunta non e'
sostituibile a quella satura, quindi aggiungere macchine veloci a un cluster che ne contiene
una lenta **peggiora** il sistema (−67.2%), perche' introduce lavoro obbligato sul nodo lento
che prima non c'era. In pull l'assegnazione avviene a domanda, a runtime: ogni macchina
riceve esattamente il lavoro che sa smaltire.

### 2. Effetto della distribuzione su ciascuno schema

Il segno dell'effetto dipende dallo schema, ed e' il risultato piu' netto dell'esperimento:
la stessa identica aggiunta di hardware degrada push del 67% e migliora pull del 70%.

La ripartizione misurata del lavoro lo mostra direttamente. Il nodo CPU-only `.11`, sette
volte piu' lento del master, riceve:

- in push **300 elaborazioni su 900 (33.3%)**, imposte dal piazzamento statico e insensibili
  alla sua velocita';
- in pull **60 su 900 (6.7%)**, cioe' quante ne chiede.

La ripartizione emergente del pull (44 / 49 / 7%) segue la capacita' delle macchine
(`1/t_s` normalizzato: 50 / 42 / 7%), con il master leggermente sotto perche' ospita anche
le 300 sintesi di `SynthOutService`.

**Riserva metodologica da dichiarare.** La coppia `PULL-LOCAL-HEAD` → `PULL-DIST-HEAD` da
sola non dimostra il punto architetturale: il 55.7% di lavoro delocalizzato produce −41.3%
di wall clock, cioe' *meno* di quanto darebbe il semplice spostamento di lavoro fuori da una
macchina satura. Il confronto probante e' `PUSH-DIST` contro `PULL-DIST-HEAD`, dove hardware,
commit, topic e numero di macchine sono identici e l'unica variabile e' la disciplina di
assegnazione. La coppia locale→distribuito misura l'effetto di *aggiungere macchine*; la
coppia push-dist→pull-dist misura l'effetto dello *schema*.

### 3. Effetto della politica di coda

`tail` e' peggiore di `head` su tutti gli assi misurati: −10.7% di throughput in locale,
−13.3% in distribuito, latenza e2e da 5 a 7 volte superiore, e bilanciamento peggiore di 7.8
punti anziche' migliore. **L'ipotesi che `tail` servisse a correggere lo squilibrio da
co-locazione e' quindi respinta dai dati.**

Il ciclo auto-alimentato di `head` esiste ed e' quantificato (il master passa da 44.3% a
36.4% del carico quando si passa a `tail`), ma non e' la causa dello squilibrio: lo
squilibrio riflette la capacita' delle macchine, ed e' desiderabile. Rimuovere il vantaggio
di co-locazione sposta lavoro dal master a `.5`, che era gia' il nodo piu' carico.

Sul throughput, il degrado non e' starvation — a regime nessun worker resta senza lavoro e
il master e' occupato al 96-98% in entrambe le politiche — ma **perdita di efficienza a
parita' di saturazione**, concentrata nell'elaborazione che chiude il virtual layer
(2.6s → 7.3s). L'interpretazione proposta e' che `tail` sincronizzi l'avanzamento dei task,
facendo collidere a ondate le chiusure di layer con le sintesi sullo stesso Ollama, mentre
`head` le serializza.

Sulla latenza, l'aumento di ~6x e' invece atteso e non e' un difetto: discende da Little con
in-flight che sale da 4.3 a 26.1, cioe' a `target_queue_size`. **`tail` non rallenta il
sistema di 6 volte, lo fa lavorare con 6 volte piu' task aperti contemporaneamente.**

### 4. Limiti della misura e cosa servirebbe per rafforzarla

- **Una sola ripetizione per configurazione.** Nessuna barra d'errore: le differenze
  di throughput sotto il 10% (in particolare push-local vs pull-local, +5.6%) non sono
  distinguibili dal rumore. Le differenze grandi (5.48x) lo sono ampiamente.
- **L'accuracy non e' interpretabile.** I sei valori stanno tra 47.0% e 55.0% con errore
  standard ~5 punti su 100 query, e le elaborazioni girano a `temperature 0.7`: tutto e'
  entro rumore. Il deployment non cambia il calcolo eseguito, quindi qualunque differenza di
  accuracy tra LOCAL e DIST **e' rumore per costruzione** e va riportata come controllo
  di sanita', non come risultato.
- **Push e pull non fanno lo stesso numero di chiamate LLM** (15 contro 12). Va dichiarato:
  incide sul confronto locale, e' trascurabile su quello distribuito.
- **Cluster di 3 macchine con un solo nodo lento.** Il risultato dipende dal grado di
  eterogeneita': con `t_s` 2.1 / 2.5 / 14.3s il rapporto tra i tetti e' 5.6x, ma su un
  cluster omogeneo sarebbe 1. Servirebbe una serie di run al variare di `max(t_s)/min(t_s)`
  per tracciare la curva invece del singolo punto.
- **La distribuzione del carico di `PUSH-DIST` non e' misurata ma dedotta** dal piazzamento
  statico (il log del driver e' andato perso). E' una deduzione esatta — le config
  `dist_fixed_configs/*.json` la determinano — ma non un dato osservato.
- **`t_s` e' ricavato dai run, non misurato a sistema scarico** con il `curl` documentato
  sopra. Le previsioni tornano entro il 3%, ma la misura diretta renderebbe il criterio
  a priori indipendente dai run che deve prevedere.
- **Il meccanismo proposto per il degrado di `tail`** (collisione sintesi/chiusura-layer) e'
  coerente con i dati ma non misurato direttamente: servirebbe strumentare il tempo di
  attesa dentro Ollama.
