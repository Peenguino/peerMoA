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
- 5.1.3 [x] Cluster: numero macchine, ruoli, specifiche HW, GPU/CPU, tok/s e tempo di
  servizio $t_s$ misurati
- 5.1.4 [x] Modello (`qwen2.5:1.5b`) e motivazione
- 5.1.5 [x] Dataset (MMLU `college_computer_science`, 100 query, split test)
- 5.1.6 [x] Parametri fissati (temperature, `target_queue_size`, `num_synth_workers`,
  sliding window, requeue policy)
- 5.1.7 [x] System prompt (ruoli mid/output, con/senza risposta precedente)
- 5.1.8 [x] Versioni software (Python pinnato via `uv`, Ollama, `requirements.txt`)
- 5.1.9 [x] Le sei configurazioni — tabella riepilogativa

### 5.2 Risultati (solo presentazione, niente interpretazione)
- 5.2.1 [x] Metriche aggregate delle sei configurazioni
- 5.2.2 [x] Distribuzione del carico tra i nodi
- 5.2.3 [x] Confronto locale vs distribuito, per schema
- 5.2.4 [x] Effetto della politica di coda

### 5.3 Discussione

> Direzione: non quattro sottosezioni indipendenti. 5.3.1→5.3.3 sono tre prove
> convergenti dello stesso risultato — perché vince `PULL-DIST-HEAD`, la sola
> configurazione a primeggiare su entrambe le metriche primarie insieme
> (throughput 0.0767 msg/s, il più alto delle sei; E2E media 56.54 s, la più
> bassa delle sei; in-flight 4.3 msg, pari al minimo) — vista da tre angolazioni
> complementari. 5.3.4 è sezione di tenuta, non lista di limiti generici (quelli
> più ampi stanno in 6.2).

- 5.3.1 [x] Push vs pull a parità di deployment — il confronto controllato (tetto
  teorico, fungibilità della capacità)

- 5.3.2 [x] Effetto della distribuzione su ciascuno schema — il segno si inverte

- 5.3.3 [x] Effetto della politica di coda — `head` non è un caso, è parte della configurazione vincente (ciclo auto-alimentato, collisioni sintesi/chiusura layer)


## 6. Conclusioni
- 6.1 [x] Sintesi del lavoro e risultati principali
- 6.2 [x] Limiti (singola ripetizione, cluster piccolo, accuracy rumorosa, $t_s$ stimato non
  a sistema scarico)
- 6.3 [x] Lavori futuri