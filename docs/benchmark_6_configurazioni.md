# Benchmark PeerMoA — 6 configurazioni

Confronto di **e2e latency** e **throughput** tra schema push e schema pull, in
deployment singolo nodo e distribuito, con le due politiche di coda del pull.

> **Regola non negoziabile:** tutti e sei i run devono girare sullo **stesso commit**.
> Un confronto tra run su codice diverso non misura l'architettura, misura la
> differenza di codice. Annotare l'hash sotto e verificarlo prima di ogni run.

**Commit di riferimento:** `________________` (`git rev-parse --short HEAD`)

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
| Modello | `________` | menu interattivo (voce "Select the model") |
| Topic MMLU | `________` | menu interattivo (voce "Select the benchmark's topic") |
| Query totali | `________` | dimensione dello split `test` del topic |
| Elaborazioni per query | 9 | push: 3 layer x 3 agenti — pull: 3 layer x 3 elaborazioni |
| Sintesi per query | 3 | una per virtual layer |
| `target_queue_size` | 25 | `pull_queueHeadService.py` |
| Consumer di sintesi | 5 | `num_synth_workers` in `pull_synthOutService.py` |
| Macchine (run DIST) | `.____` master, `.____`, `.____` | IP effettivi al momento del run |

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

| Configurazione | Cartella di log | E2E media (s) | E2E mediana (s) | E2E p95 (s) | Throughput (msg/s) | Wall clock (s) | Accuracy (%) |
|---|---|---|---|---|---|---|---|
| `PUSH-LOCAL` | | | | | | | |
| `PUSH-DIST` | | | | | | | |
| `PULL-LOCAL-HEAD` | | | | | | | |
| `PULL-DIST-HEAD` | | | | | | | |
| `PULL-LOCAL-TAIL` | | | | | | | |
| `PULL-DIST-TAIL` | | | | | | | |

### Distribuzione del carico

Il punto critico: quanto lavoro e' stato davvero eseguito fuori dal master. Senza
questa colonna un guadagno di throughput non e' attribuibile alla distribuzione.

| Configurazione | Elab. nodo 1 | Elab. nodo 2 | Elab. nodo 3 | % sul nodo piu' carico | Chiamate LLM totali sul master |
|---|---|---|---|---|---|
| `PUSH-LOCAL` | | | | | |
| `PUSH-DIST` | | | | | |
| `PULL-LOCAL-HEAD` | | | | | |
| `PULL-DIST-HEAD` | | | | | |
| `PULL-LOCAL-TAIL` | | | | | |
| `PULL-DIST-TAIL` | | | | | |

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

### Guadagno atteso vs osservato

Il controllo che smaschera un guadagno solo apparente: se la riduzione del wall
clock coincide con la frazione di lavoro delocalizzata, il vantaggio non e'
architetturale, e' solo lavoro tolto alla macchina satura.

| Coppia confrontata | Lavoro delocalizzato (%) | Riduzione wall clock (%) | Delta throughput (%) | Attribuibile alla distribuzione? |
|---|---|---|---|---|
| `PUSH-LOCAL` → `PUSH-DIST` | | | | |
| `PULL-LOCAL-HEAD` → `PULL-DIST-HEAD` | | | | |
| `PULL-LOCAL-TAIL` → `PULL-DIST-TAIL` | | | | |

### Effetto della politica di coda

| Coppia confrontata | Delta E2E media (%) | Delta throughput (%) | Delta squilibrio (punti %) |
|---|---|---|---|
| `PULL-LOCAL-HEAD` → `PULL-LOCAL-TAIL` | | | |
| `PULL-DIST-HEAD` → `PULL-DIST-TAIL` | | | |

Attesa da verificare: `tail` peggiora la latenza e2e (piu' work in progress) e
migliora il bilanciamento. Se il bilanciamento non migliora, la causa dello
squilibrio non e' la politica di reinserimento e va cercata altrove.

---

## Note sulla lettura dei dati

- **Latenza e throughput non si muovono insieme.** Per Little, in-flight medi =
  latenza media x throughput. Due run con throughput uguale e latenza diversa hanno
  semplicemente lavorato a livelli di concorrenza diversi: vanno confrontati solo
  se il numero di query in volo e' comparabile.
- **Il throughput riportato e' arrotondato a 2 decimali** (`{:.2f}` in
  `pull_synthOutService.py`), quindi a questi ritmi tutto collassa su `0.03 msg/s`.
  Ricalcolarlo come `query completate / wall clock` invece di leggerlo dal log.
- **L'accuracy non e' deterministica.** Il `seed=2` fissa il campionamento del
  dataset, non l'output del modello: le elaborazioni girano a `temperature 0.7`.
  Con 100 query lo scarto tipico e' di diversi punti percentuali; non trarre
  conclusioni sulla qualita' senza ripetizioni.
- **Lo skew di clock tra macchine non falsa le metriche** ma rende inutile
  correlare i timestamp tra log di macchine diverse: `start_time` e chiusura sono
  entrambi marcati sul master (`pull_queueHeadService.py`, `pull_synthOutService.py`).

---

## Conclusioni

_(da scrivere dopo aver compilato le tabelle)_

1. Push vs pull a parita' di deployment:
2. Effetto della distribuzione su ciascuno schema:
3. Effetto della politica di coda:
4. Limiti della misura e cosa servirebbe per rafforzarla:
