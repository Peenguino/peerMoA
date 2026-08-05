# Pull distribuito su piu' macchine fisiche (fixed placement)

Topologia a 3 macchine, 9 elaborazioni per query (3 virtual layer x 3 elaborazioni),
a parita' di carico con il push (3 layer x 3 agenti).

| Config                       | Attori ospitati                                 |
| ---------------------------- | ----------------------------------------------- |
| `machine_master_pull.json`   | `QueueHeadNode`, `SynthOutNode`, `ElabMidNode-1` |
| `machine_worker_2_pull.json` | `ElabMidNode-2`                                  |
| `machine_worker_3_pull.json` | `ElabMidNode-3`                                  |

I nomi dei file e le tag risorsa sono indipendenti dagli indirizzi IP: il ruolo di
una macchina dipende solo da quale config le passi.

## Pre-requisiti su ogni macchina

- Ollama in esecuzione con lo stesso modello scaricato (es. `ollama pull qwen2.5:1.5b`).
  Basta l'ascolto su `127.0.0.1:11434`: ogni `ElabMidService` usa l'Ollama della
  propria macchina, quindi non serve esporlo sulla LAN.
- Stesso commit del repo, `.venv` creato e dipendenze installate.
- Porta 6379 raggiungibile dai worker verso il master.

## Avvio

Prima il master, che stampa l'IP rilevato e la riga esatta da usare sui worker:

```bash
./master_fixed_start.sh machine_master_pull.json
```

L'IP del master viene ricavato automaticamente dalla default route e validato
contro le interfacce locali, quindi un nuovo lease DHCP non rompe il run.
Per forzarlo: `PEERMOA_MASTER_IP=x.x.x.x ./master_fixed_start.sh ...`.

Poi i due worker, con l'IP stampato dal master:

```bash
PEERMOA_MASTER_IP=<ip-master> ./worker_fixed_start.sh machine_worker_2_pull.json
PEERMOA_MASTER_IP=<ip-master> ./worker_fixed_start.sh machine_worker_3_pull.json
```

Ray accetta la connessione dei worker gia' dopo `ray start --head`, senza attendere
`main.py`. Se il master non e' ancora pronto il worker esce subito con un messaggio
esplicito invece di attendere il timeout GCS.

Nel menu interattivo sul master: applicazione `pullApplication`, numero di worker
node per lo schema Pull = 3.

## Ollama host mapping (opzionale)

`dist/dist_fixed_configs/pull_ollama_hosts.json` mappa ogni `ElabMidService-N` a un
URL Ollama esplicito. **Non viene usato in questo flusso**: entrambi gli script fanno
`unset` di `PEERMOA_PULL_OLLAMA_HOSTS` e `PEERMOA_PULL_OLLAMA_HOSTS_FILE`, e ogni
servizio ricade sul default `http://127.0.0.1:11434` — che e' il comportamento
corretto quando gli attori sono gia' distribuiti su macchine fisiche diverse.

Serve solo se vuoi puntare a Ollama remoti da un unico processo (es. pull
non distribuito con inferenza su piu' host), esportando:

```bash
export PEERMOA_PULL_OLLAMA_HOSTS_FILE=/path/to/pull_ollama_hosts.json
```

In quel caso gli IP nel file vanno tenuti allineati a mano.

## Verifica del placement

- Log del run sul master: `./logs/PULL_<timestamp>/simulation.log`.
- Su ciascun worker, `ollama ps` durante il run deve mostrare attivita': conferma
  che l'attore e' stato schedulato li' e non sul master.
