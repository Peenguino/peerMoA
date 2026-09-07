# Outline tesi — peerMoA

> Documento di lavoro per la struttura della tesi. Non contiene testo definitivo,
> solo sotto-capitoli e note su cosa deve andarci e da dove viene il materiale.
> Target: 40-50 pagine di corpo tesi.

**Framing centrale (da mantenere in tutti i capitoli):** il **push** è l'architettura
Mixture-of-Agents *originale* (repo/paper TogetherComputer/MoA), qui riprodotta come
`LayerApplication`. Il **pull** (`pull_layerApplication`, coda condivisa, virtual layer,
policy `head`/`tail`) è un'estensione **proposta dai relatori** e **validata
sperimentalmente in questa tesi** contro l'originale, su cluster fisico eterogeneo. Non è
un confronto tra due schemi noti in letteratura: è la prima verifica empirica di
un'ipotesi di scheduling distribuito per MoA.

## Budget pagine indicativo

| Capitolo | pp |
|---|---|
| 1. Introduzione | 3-4 |
| 2. Background | 6-8 |
| 3. Stato dell'arte | 6-8 |
| 4. Metodologia | 8-10 |
| 5. Esperimenti (setup + risultati + discussione) | 15-19 |
| 6. Conclusioni | 3-4 |
| Bibliografia | non conteggiata |

---





## 1. Introduzione - 4 pagine
- [x] 1.1 Contesto — proliferazione LLM, costo dell'inferenza di modelli grandi, spinta
  verso small/local model, MoA come modo di recuperare qualità componendo modelli deboli.
- [x] 1.2 Problema considerato — l'architettura MoA originale non affronta il deploy
  distribuito su hardware eterogeneo; il piazzamento statico non si adatta a nodi di
  velocità diversa.
- [x] 1.3 Obiettivo della tesi (frase letterale) — validare sperimentalmente un'estensione
  a scheduling dinamico (pull, coda condivisa) dell'architettura MoA originale (push,
  piazzamento statico), misurando throughput ed e2e latency su cluster omogeneo ed
  eterogeneo.
- [x] 1.4 Struttura della tesi — un paragrafo a capitolo.

## 2. Background - 8 pagine
- [x] 2.1 LLM e inferenza locale — perché SLM (`qwen2.5:1.5b`) + Ollama.
- [x] 2.2 Mixture-of-Agents — layer, proposer (alta temperatura) vs aggregator (bassa
  temperatura); solo concetto, il dettaglio implementativo va in Metodologia.
- [x] 2.3 Sistemi multi-agente e loro distribuzione — perché distribuire (scalabilità,
  hardware eterogeneo, edge), sfide generali (comunicazione, scheduling, bilanciamento).
- [x] 2.4 ECLYPSE — modello a componenti (Service/Application/Infrastructure/DeployStrategy),
  cosa fornisce sopra Ray, perché è stato scelto.

## 3. Stato dell'arte
- [x] 3.1 Mixture-of-Agents — **fonte primaria: repo + paper TogetherComputer/MoA**.
  Descrivere l'architettura *come proposta nell'originale* (composizione statica dei
  layer, single-machine): è la base concettuale dello schema push.
- [x] 3.2 Framework di orchestrazione multi-agente per LLM — AutoGen, CrewAI, LangGraph:
  cosa offrono, perché non risolvono lo scheduling distribuito su hardware eterogeneo.
- [x] 3.3 Scheduling push/pull in sistemi distribuiti — letteratura generale (work-stealing,
  code pull-based, scheduling cloud/serverless) a supporto della policy pull, che è
  ipotesi dei relatori e non della letteratura MoA.
- [x] 3.4 Framework per edge/fog computing e simulazione — ECLYPSE come artefatto di ricerca.
- [x] 3.5 Posizionamento della tesi — **gap**: l'originale MoA non discute deploy distribuito
  su hardware eterogeneo; il pull è un'estensione proposta dai relatori; questa tesi ne
  fornisce la prima validazione sperimentale contro il push originale.

## 4. Metodologia
- [x] 4.1 Architettura generale e principi comuni
  - peerMoA, ruolo di ECLYPSE (richiamo concreto di Service/Application/Infrastructure/Strategy), Ollama come motore condiviso
  - cosa è davvero comune alle due famiglie: ciclo di vita bootstrap→ingestion MMLU→scoring→terminazione (SIGINT), presente in
    entrambe anche se implementato da classi diverse (HeadBenchmarkService/TailBenchmarkService vs QueueHeadService/SynthOutService) —
    nominare qui questa dualità di ruoli senza ancora scendere nei dettagli

- [x] 4.2 Schema Push — LayerApplication
  - [x] 4.2.1 Topologia a layer statici — grafo lineare, un'istanza per (layer, agente), piazzamento = ruolo logico
  - [x] 4.2.2 Servizi — HeadBenchmarkService/TailBenchmarkService (sliding window, ACK, scoring), InputNodeService (broadcast),
    MidNodeService (proposer), OutputNodeService (aggregator: char-synth se ultimo layer, altrimenti string-synth per il layer
    successivo)                                                                                
  - [x] 4.2.3 Comunicazione — MPI bcast/recv, messageDictTemplate push (struttura e semantica dei campi)
  - [x] 4.2.4 Strategia di deploy — staticLayerStrat, mapping esplicito nome-per-nome
  - [x] 4.2.5 SingleAgentApplication come caso degenere del push (baseline concettuale a 1 nodo, non benchmarkata)

- [x] 4.3 Schema Pull — pull_layerApplication
  - [x] 4.3.1 Topologia a coda condivisa — grafo a hub, worker generici e intercambiabili
  - [x] 4.3.2 Servizi — QueueHeadService (coda, target_queue_size, /pull, /requeue, policy head/tail), ElabMidService (worker, polling,
    max_elaborations), SynthOutService (/synthesize, pool num_synth_workers, char-synth finale o re-injection in coda)
  - [x] 4.3.3 Il concetto di virtual layer — come lo stato del messaggio sostituisce la topologia statica, e perché questo preserva
    l'equivalenza semantica col MoA originale
  - [x] 4.3.4 Comunicazione — REST, polling, messageDictTemplate pull (differenze di campo rispetto al push)
  - [x] 4.3.5 Strategia di deploy — pull_layerStrat: chiarire esplicitamente che il piazzamento servizio↔nodo resta statico come nel push;
    ciò che è "pull" è solo l'assegnamento task→worker a runtime

- [x] 4.4 Confronto strutturale push vs pull (sintesi)
  - [x] tabella riassuntiva: topologia, granularità delle istanze, protocollo, backpressure, dove vive la nozione di "layer", cosa resta
    statico in entrambi
  - [x] qui si guadagna la vera motivazione del confronto: a parità di infrastruttura fisica, le due Application implementano la stessa
    semantica MoA con meccanismi di scheduling radicalmente diversi

- [x] 4.5 Metriche
  - [x] invariato nella sostanza (e2e latency, throughput, in-flight/Little, accuracy, distribuzione del carico — solo definizioni), ma
    nota: il punto di calcolo effettivo differisce (TailBenchmarkService per push, SynthOutService per pull) — una riga a parte, non
    una sezione

## 5. Esperimenti

### 5.1 Setup sperimentale
- 5.1.1 [x] Le due versioni del sistema e perché confrontarle
- 5.1.2 [x] Metriche di valutazione
- 5.1.3 Cluster: numero macchine, ruoli, specifiche HW, GPU/CPU, tok/s e tempo di
  servizio $t_s$ misurati
- 5.1.4 Modello (`qwen2.5:1.5b`) e motivazione
- 5.1.5 Dataset (MMLU `college_computer_science`, 100 query, split test)
- 5.1.6 Parametri fissati (temperature, `target_queue_size`, `num_synth_workers`,
  sliding window, requeue policy)
- 5.1.7 System prompt (ruoli mid/output, con/senza risposta precedente)
- 5.1.8 Versioni software (Python pinnato via `uv`, Ollama, `requirements.txt`)
- 5.1.9 Le sei configurazioni — tabella riepilogativa
- 5.1.10 Procedura e criteri di validità (stesso commit, verifica dai log)

### 5.2 Risultati (solo presentazione, niente interpretazione)
- 5.2.1 Metriche aggregate delle sei configurazioni
- 5.2.2 Distribuzione del carico tra i nodi
- 5.2.3 Confronto locale vs distribuito, per schema
- 5.2.4 Effetto della politica di coda

### 5.3 Discussione
- 5.3.1 Push vs pull a parità di deployment (tetto teorico, fungibilità della capacità)
- 5.3.2 Effetto della distribuzione su ciascuno schema
- 5.3.3 Effetto della politica di coda (ciclo auto-alimentato, collisioni
  sintesi/chiusura layer)
- 5.3.4 Validità e limiti della misura (singola ripetizione, accuracy rumorosa, chiamate
  LLM non pari, riserva metodologica sul confronto locale→dist)

> Nota: `docs/benchmark_6_configurazioni.md` è già un draft di 5.2+5.3: da ristrutturare
> in prosa per i capitoli, non da riscrivere da zero.

## 6. Conclusioni
- 6.1 Sintesi del lavoro e risultati principali
- 6.2 Limiti (singola ripetizione, cluster piccolo, accuracy rumorosa, $t_s$ stimato non
  a sistema scarico)
- 6.3 Lavori futuri (repliche multiple, cluster più grande/eterogeneo, policy ibride,
  misura diretta di $t_s$, instrumentazione tempo di coda in Ollama, modelli più grandi,
  altri topic MMLU)
- 6.4 Ringraziamenti

## Bibliografia
Da popolare almeno con: paper MoA originale (TogetherComputer), paper ECLYPSE, Ollama,
MMLU (Hendrycks et al.), Ray, letteratura scheduling push/pull citata in 3.3.

---

## Aperti / TODO
- [ ] Raccogliere le fonti per 3.2/3.3/3.4 (framework multi-agente, letteratura
      scheduling push/pull, eventuali altri framework edge/fog oltre ECLYPSE).
- [ ] Verificare se il repo/paper TogetherComputer discute in qualche punto deploy
      multi-macchina (per essere precisi nel gap statement di 3.5).
- [ ] Decidere se 5.2 include grafici (consigliato: almeno throughput/latency a barre
      per le 6 config, e un grafico di distribuzione del carico per nodo).

---

## Grafici proposti per il Capitolo 5

Selezionati 10 dei candidati iniziali (i restanti 5 — scatter in-flight/E2E, tetto
teorico vs osservato, effetto della politica di coda, durata elaborazione sul
master, capacita' vs quota osservata — sono stati scartati). Tutti e 10 sono
generati come immagini PNG e gia' pronti da guardare e importare, non solo
descritti. Script sorgente:
[`docs/scripts/generate_benchmark_charts.py`](scripts/generate_benchmark_charts.py)
(dati trascritti a mano da `benchmark_6_configurazioni.md`; se il documento cambia,
aggiornare i dizionari nello script). Per rigenerarli dopo una modifica:

```bash
uv run --with matplotlib python docs/scripts/generate_benchmark_charts.py
```

I file finiscono in `docs/img/benchmark_charts/`. Palette e stile seguono la skill
`dataviz` del progetto (colore fisso per schema — blu=push, arancio=pull head,
acqua=pull tail — cosi' l'occhio lo riconosce da un grafico all'altro; niente
doppio asse; scale indipendenti quando due metriche vivono a ordini di grandezza
diversi). Ogni voce riporta cosa dimostra e a quale sotto-sezione dell'outline si
aggancia, cosi' la selezione si puo' fare senza tornare al documento sorgente.
Segnati con **[core]** i candidati che coprono un punto che il capitolo fa comunque
fatica a non avere; gli altri sono rinforzi opzionali.

1. **[core] Throughput per le 6 configurazioni** — la metrica primaria del
   documento. Sezione 5.2.1.
   ![Throughput per le 6 configurazioni](img/benchmark_charts/g01_throughput_6config.png)

2. **E2E latency (media/mediana/p95) per le 6 configurazioni**, scala log — stessa
   codifica colore del grafico 1 cosi' i due si leggono in coppia. Sezione 5.2.1.
   ![E2E latency media/mediana/p95](img/benchmark_charts/g02_e2e_latency_mean_median_p95.png)

3. **E2E media e in-flight (Little), piccoli multipli** — due pannelli impilati
   (stesso ordine di configurazioni), non un doppio asse: rende visivo il punto che
   il documento sottolinea esplicitamente, che la latenza E2E tra i tre run locali
   (230/97/592s) e' fuorviante senza gli in-flight (9.8/4.4/23.8), che la spiegano
   quasi per intero. Sezione 5.2.1, richiamato in 5.3.4 (limiti).
   ![E2E media e in-flight, piccoli multipli](img/benchmark_charts/g03_e2e_mean_and_inflight_panels.png)

4. **[core] Distribuzione del carico, barre impilate al 100%** — il contrasto
   strutturale centrale: push sempre 33/33/33 esatto, pull sbilanciato in modo
   diverso tra head e tail. Sezione 5.2.2.
   ![Distribuzione del carico, impilate al 100%](img/benchmark_charts/g05_load_distribution_stacked.png)

5. **[core] PUSH-DIST vs PULL-DIST-HEAD, per nodo + throughput** — il confronto che
   il documento stesso isola come quello che "porta il risultato" (stesso cluster,
   stesso commit, unica variabile la disciplina di assegnazione). Sezioni 5.2.2 e
   5.3.1.
   ![PUSH-DIST vs PULL-DIST-HEAD per nodo](img/benchmark_charts/g06_push_dist_vs_pull_dist_head.png)

6. **[core] Slope chart: throughput LOCAL → DIST per schema** — l'effetto opposto
   della distribuzione (push scende, pull sale) in un colpo solo, il risultato piu'
   netto dell'esperimento secondo le conclusioni del documento. Sezioni 5.2.3 e
   5.3.2.
   ![Slope chart local to dist](img/benchmark_charts/g07_slope_local_to_dist.png)

7. **Guadagno atteso vs osservato** (lavoro delocalizzato % / riduzione wall clock %
   / delta throughput %), piccoli multipli per coppia — include anche
   `PULL-TAIL LOCAL→DIST`, non presente nella tabella del documento sorgente (riga
   lasciata vuota li'): valori calcolati qui, 63.6 / 39.5 / 65.4, con lo stesso
   schema di lettura delle altre due righe. Rende visivo il test che smaschera un
   guadagno solo apparente. Sezioni 5.2.3/5.3.2.
   ![Guadagno atteso vs osservato](img/benchmark_charts/g09_expected_vs_observed_gain.png)

8. **Accuracy per le 6 configurazioni, con barra d'errore ~5 punti** — comunica
   visivamente, invece che solo a parole, che le differenze di accuracy tra le sei
   configurazioni sono entro rumore statistico e non vanno lette come risultato.
   Utile in 5.3.4 (limiti della misura).
   ![Accuracy con barra d'errore](img/benchmark_charts/g12_accuracy_with_error_bars.png)

9. **Wall clock per le 6 configurazioni** — non aggiunge un'informazione
   concettualmente nuova rispetto al throughput (sono l'uno l'inverso
   proporzionale dell'altro a query fisse), ma da' la sensazione di "quanto e'
   durato davvero" un run; utile se in 5.1.9 vuoi motivare perche' una sola
   ripetizione per configurazione.
   ![Wall clock per le 6 configurazioni](img/benchmark_charts/g13_wallclock_6config.png)

10. **Caratterizzazione del cluster: tempo di servizio `t_s` per macchina** — non e'
    un grafico di risultati ma di setup: quantifica l'eterogeneita' dichiarata del
    cluster prima ancora di mostrare l'effetto sui run. Il valore di `.11` e'
    tratteggiato e marcato con `*` perche' ricavato dal throughput del run, non
    misurato a sistema scarico con `curl` come gli altri due (il documento non
    riporta i tok/s per nessuna macchina, quindi quella colonna e' stata omessa
    rispetto all'idea iniziale). Andrebbe in 5.1.2, non in 5.2/5.3.
    ![t_s per macchina](img/benchmark_charts/g14_ts_per_machine.png)
