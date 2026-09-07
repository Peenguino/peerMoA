"""
Genera le figure statiche (PNG) per il Capitolo 5 della tesi, a partire dai
dati riportati in docs/benchmark_6_configurazioni.md.

I dati sono trascritti a mano dalle tabelle del documento (nessun parsing di
markdown): se il documento viene aggiornato con nuovi run, aggiornare i
dizionari qui sotto di conseguenza.

Uso:
    uv run --with matplotlib python docs/scripts/generate_benchmark_charts.py

Le immagini vengono scritte in docs/img/benchmark_charts/g01_*.png ... g15_*.png.
"""

import math
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --------------------------------------------------------------------------
# Palette (skill dataviz — palette.md), modalita' chiara: le figure vanno
# stampate/incollate in un PDF di tesi su sfondo bianco.
# --------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

# Colore per schema (identita', fissa in tutte le figure che confrontano
# schemi/configurazioni): slot 1/2/3 della palette categorica, gli unici tre
# che validano tutte le coppie in entrambe le modalita'.
C_PUSH = "#2a78d6"       # blue
C_PULL_HEAD = "#eb6834"  # orange
C_PULL_TAIL = "#1baf7a"  # aqua

# Rampa sequenziale blu, per grandezze ordinali senza identita' propria
# (posizione nodo 1/2/3 nel grafico di distribuzione del carico).
SEQ_NODE = ["#6da7ec", "#2a78d6", "#184f95"]  # step 300 / 450 / 600

# Colori dedicati alle figure "metrica" (9, 10) dove l'entita' e' la metrica
# stessa e non lo schema — slot 4/5/7 della palette, cosi' da non sovrapporsi
# al significato di blue/orange/aqua usato altrove.
C_METRIC_A = "#4a3aa7"  # violet — lavoro delocalizzato / capacita' attesa
C_METRIC_B = "#eda100"  # yellow — riduzione wall clock / delta E2E
C_METRIC_C = "#e87ba4"  # magenta — delta throughput

FONT = "DejaVu Sans"
plt.rcParams.update({
    "font.family": FONT,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "font.size": 6.5,
})

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "img", "benchmark_charts")
os.makedirs(OUT_DIR, exist_ok=True)


def style_axes(ax, y_grid=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="both", length=0)
    if y_grid:
        ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)


def bar_labels(ax, bars, fmt="{:.0f}", dy=0, color=INK_SECONDARY, fontsize=9):
    for b in bars:
        h = b.get_height()
        va = "bottom" if h >= 0 else "top"
        off = dy if h >= 0 else -dy
        ax.annotate(
            fmt.format(h),
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 3 * (1 if h >= 0 else -1) + off),
            textcoords="offset points",
            ha="center", va=va,
            fontsize=fontsize, color=color,
        )


def savefig(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("scritto:", os.path.relpath(path))


# --------------------------------------------------------------------------
# Dati (da docs/benchmark_6_configurazioni.md)
# --------------------------------------------------------------------------
CONFIGS = [
    "PUSH-LOCAL", "PUSH-DIST",
    "PULL-HEAD-LOCAL", "PULL-HEAD-DIST",
    "PULL-TAIL-LOCAL", "PULL-TAIL-DIST",
]
CONFIG_LABELS = [
    "PUSH\nLOCAL", "PUSH\nDIST",
    "PULL-HEAD\nLOCAL", "PULL-HEAD\nDIST",
    "PULL-TAIL\nLOCAL", "PULL-TAIL\nDIST",
]
SCHEMA = ["push", "push", "pull-head", "pull-head", "pull-tail", "pull-tail"]
DEPLOY = ["local", "dist", "local", "dist", "local", "dist"]
SCHEMA_COLOR = {"push": C_PUSH, "pull-head": C_PULL_HEAD, "pull-tail": C_PULL_TAIL}
CONFIG_COLORS = [SCHEMA_COLOR[s] for s in SCHEMA]
CONFIG_ALPHA = [0.5 if d == "local" else 1.0 for d in DEPLOY]

E2E_MEAN = [229.89, 692.85, 97.39, 56.54, 592.01, 392.02]
E2E_MEDIAN = [226.52, 692.98, 90.61, 47.52, 608.05, 357.00]
E2E_P95 = [332.25, 904.49, 157.83, 105.97, 710.36, 565.37]
THROUGHPUT = [0.0426, 0.0140, 0.0450, 0.0767, 0.0402, 0.0665]
INFLIGHT = [9.8, 9.7, 4.4, 4.3, 23.8, 26.1]
WALLCLOCK = [2345.5, 7151.8, 2220.5, 1304.3, 2485.9, 1504.2]
ACCURACY = [52.0, 47.0, 47.5, 50.0, 50.5, 55.0]
ACCURACY_ERR = math.sqrt(0.5 * 0.5 / 100) * 100  # ~5 punti percentuali

# Distribuzione del carico: (nodo1, nodo2, nodo3) — per i run LOCAL sono le
# tre istanze di servizio sulla stessa macchina, per i run DIST sono le tre
# macchine fisiche .12 / .5 / .11 nell'ordine dato dal documento.
LOAD = {
    "PUSH-LOCAL": (900, None, None),
    "PUSH-DIST": (300, 300, 300),
    "PULL-HEAD-LOCAL": (294, 302, 304),
    "PULL-HEAD-DIST": (399, 441, 60),
    "PULL-TAIL-LOCAL": (305, 278, 317),
    "PULL-TAIL-DIST": (328, 511, 61),
}
NODE_TAG_DIST = [".12 master", ".5", ".11 (CPU)"]

# --------------------------------------------------------------------------
# G1 — Throughput per le 6 configurazioni - OK
# --------------------------------------------------------------------------
def g01_throughput():
    fig, ax = plt.subplots(figsize=(7.2, 5))
    x = range(len(CONFIGS))
    bars = ax.bar(x, THROUGHPUT, color=CONFIG_COLORS, alpha=None, width=0.325, zorder=3)
    for b, a in zip(bars, CONFIG_ALPHA):
        b.set_alpha(a)
        b.set_edgecolor(INK_PRIMARY)
        b.set_linewidth(0.6)
    bar_labels(ax, bars, fmt="{:.4f}")
    ax.set_xticks(list(x))
    ax.set_xticklabels(CONFIG_LABELS, fontsize=9)
    ax.set_ylabel("Throughput (msg/s)")
    ax.set_ylim(top=0.095)
    ax.set_title("Throughput per Configurazione", 
        loc="center",
        pad=4)
    style_axes(ax)
    legend_elems = [
        Patch(facecolor=C_PUSH, label="push"),
        Patch(facecolor=C_PULL_HEAD, label="pull head"),
        Patch(facecolor=C_PULL_TAIL, label="pull tail"),
        Patch(facecolor=INK_MUTED, alpha=0.5, label="LOCAL"),
        Patch(facecolor=INK_MUTED, alpha=1.0, label="DIST"),
    ]
    ax.legend(handles=legend_elems, loc="upper center", bbox_to_anchor=(0.5, -0.18),
              ncol=3, frameon=False, fontsize=8.5)
    savefig(fig, "g01_throughput_6config.png")


# --------------------------------------------------------------------------
# G2 — E2E latency (media/mediana/p95), scala log
# --------------------------------------------------------------------------
def g02_e2e_latency():
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    n = len(CONFIGS)
    width = 0.25
    x = list(range(n))
    metrics = [("Media", E2E_MEAN, 1.0), ("Mediana", E2E_MEDIAN, 0.7), ("P95", E2E_P95, 0.42)]
    for i, (label, vals, alpha) in enumerate(metrics):
        xs = [xi + (i - 1) * width for xi in x]
        bars = ax.bar(xs, vals, width=width * 0.92,
                       color=[CONFIG_COLORS[j] for j in x], alpha=alpha,
                       edgecolor=INK_PRIMARY, linewidth=0.5, zorder=3)
    ax.set_yscale("log")
    ax.set_ylabel("E2E latency (s), scala log")
    ax.set_xticks(x)
    ax.set_xticklabels(CONFIG_LABELS, fontsize=9)
    ax.set_title("Latenza E2E — media, mediana, p95", loc="center")
    style_axes(ax)
    # Il colore delle barre codifica lo schema (blu/arancio/acqua, come in Fig. 1);
    # le tre metriche sono codificate dall'opacita' dello stesso colore, non da un
    # colore diverso — spiegato in testo invece che con una legenda a swatch grigi,
    # posizionato in coordinate assi (non dati) subito sotto le etichette x, cosi'
    # resta vicino al grafico invece che sperso in un punto qualunque della scala log.
    ax.text(0.5, -0.14, "In ordine di opacità: Media, Mediana e P95",
            transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
            color=INK_MUTED, style="italic")
    savefig(fig, "g02_e2e_latency_mean_median_p95.png")


# --------------------------------------------------------------------------
# G3 — E2E media + in-flight, piccoli multipli (NO doppio asse)
# --------------------------------------------------------------------------
def g03_e2e_vs_inflight_panels():
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.6), sharex=True)
    x = range(len(CONFIGS))

    bars0 = axes[0].bar(x, E2E_MEAN, color=CONFIG_COLORS, width=0.325, zorder=3)
    for b, a in zip(bars0, CONFIG_ALPHA):
        b.set_alpha(a); b.set_edgecolor(INK_PRIMARY); b.set_linewidth(0.6)
    bar_labels(axes[0], bars0, fmt="{:.0f}s")
    axes[0].set_ylabel("E2E media (s)")
    axes[0].set_title("Latenza E2E media e in-flight (Little) per configurazione",
                       loc="center", pad=12)
    style_axes(axes[0])

    bars1 = axes[1].bar(x, INFLIGHT, color=CONFIG_COLORS, width=0.325, zorder=3)
    for b, a in zip(bars1, CONFIG_ALPHA):
        b.set_alpha(a); b.set_edgecolor(INK_PRIMARY); b.set_linewidth(0.6)
    bar_labels(axes[1], bars1, fmt="{:.1f}")
    axes[1].set_ylabel("In-flight (Little)")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(CONFIG_LABELS, fontsize=9)
    style_axes(axes[1])

    fig.text(0.5, -0.01,
              "La latenza alta coincide con in-flight alto, non con uno schema intrinsecamente piu' lento.",
              ha="center", fontsize=8.5, color=INK_MUTED, style="italic")
    savefig(fig, "g03_e2e_mean_and_inflight_panels.png")

# --------------------------------------------------------------------------
# G5 — Distribuzione del carico, barre impilate al 100%
# --------------------------------------------------------------------------
def g05_load_stacked_100():
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    x = range(len(CONFIGS))
    bottoms = [0.0] * len(CONFIGS)
    for node_idx in range(3):
        shares = []
        for cfg in CONFIGS:
            vals = LOAD[cfg]
            total = sum(v for v in vals if v is not None)
            v = vals[node_idx]
            shares.append(0.0 if v is None else 100.0 * v / total)
        bars = ax.bar(x, shares, bottom=bottoms, width=0.6,
                       color=SEQ_NODE[node_idx], edgecolor=SURFACE, linewidth=1.5,
                       zorder=3, label=f"Nodo {node_idx + 1}")
        for b, s, bot in zip(bars, shares, bottoms):
            if s > 4:
                ax.text(b.get_x() + b.get_width() / 2, bot + s / 2, f"{s:.1f}%",
                        ha="center", va="center", fontsize=8.5,
                        color="white" if node_idx > 0 else INK_PRIMARY)
        bottoms = [bo + s for bo, s in zip(bottoms, shares)]
    ax.set_ylim(0, 100)
    ax.set_ylabel("Quota di elaborazioni (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(CONFIG_LABELS, fontsize=9)
    ax.set_title("Distribuzione del carico tra nodi (quota %)", loc="center", pad=12)
    style_axes(ax, y_grid=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=9)
    fig.text(0.5, -0.1,
              "Distribuzione su Nodi Logici.\n"
              "PUSH-LOCAL: 900 elaborazioni su un'unica macchina. Run DIST: nodo 1/2/3 = .12 (master) / .5 / .11 (CPU).",
              ha="center", fontsize=8, color=INK_MUTED, style="italic")
    savefig(fig, "g05_load_distribution_stacked.png")


# --------------------------------------------------------------------------
# G6 — PUSH-DIST vs PULL-DIST-HEAD, per nodo
# --------------------------------------------------------------------------
def g06_push_vs_pull_head_dist():
    push_vals = LOAD["PUSH-DIST"]
    pull_vals = LOAD["PULL-HEAD-DIST"]
    push_pct = [100 * v / sum(push_vals) for v in push_vals]
    pull_pct = [100 * v / sum(pull_vals) for v in pull_vals]

    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    x = range(3)
    width = 0.32
    b1 = ax.bar([xi - width / 2 for xi in x], push_pct, width=width, color=C_PUSH,
                edgecolor=INK_PRIMARY, linewidth=0.6, zorder=3, label="PUSH-DIST")
    b2 = ax.bar([xi + width / 2 for xi in x], pull_pct, width=width, color=C_PULL_HEAD,
                edgecolor=INK_PRIMARY, linewidth=0.6, zorder=3, label="PULL-DIST-HEAD")
    bar_labels(ax, b1, fmt="{:.1f}%")
    bar_labels(ax, b2, fmt="{:.1f}%")
    ax.set_xticks(list(x))
    ax.set_xticklabels(NODE_TAG_DIST)
    ax.set_ylabel("Quota di elaborazioni (%)")
    ax.set_ylim(0, 60)
    ax.set_title("PUSH-DIST vs PULL-DIST-HEAD",
                 loc="center", pad=8)
    style_axes(ax)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    fig.text(0.5, -0.05,
              "Throughput: PUSH-DIST 0.0140 msg/s  →  PULL-DIST-HEAD 0.0767 msg/s  (5.48×)",
              ha="center", fontsize=8, color=INK_PRIMARY)
    savefig(fig, "g06_push_dist_vs_pull_dist_head.png")


# --------------------------------------------------------------------------
# G7 — Slope chart LOCAL -> DIST per schema
# --------------------------------------------------------------------------
def g07_slope_local_dist():
    fig, ax = plt.subplots(figsize=(6.8, 5.4))
    pairs = [
        ("push", THROUGHPUT[0], THROUGHPUT[1], C_PUSH),
        ("pull head", THROUGHPUT[2], THROUGHPUT[3], C_PULL_HEAD),
        ("pull tail", THROUGHPUT[4], THROUGHPUT[5], C_PULL_TAIL),
    ]
    for label, v_local, v_dist, color in pairs:
        ax.plot([0, 1], [v_local, v_dist], color=color, linewidth=2.4, marker="o",
                markersize=8, zorder=3, markeredgecolor=INK_PRIMARY, markeredgewidth=0.6)

    # Le tre etichette LOCAL sono ravvicinate (0.040-0.045): le scaglioniamo in
    # verticale per rango, cosi' non si sovrappongono, ed evitiamo di ripetere
    # il nome dello schema li' (lo mette la legenda in alto).
    local_order = sorted(range(len(pairs)), key=lambda i: pairs[i][1])
    offsets = {rank: off for rank, off in zip(local_order, [-20, 0, 20])}
    for i, (label, v_local, v_dist, color) in enumerate(pairs):
        ax.annotate(f"{v_local:.4f}", (0, v_local), xytext=(-12, offsets[i]),
                    textcoords="offset points", ha="right", va="center", fontsize=9,
                    color=color, fontweight="bold")
        delta = 100 * (v_dist - v_local) / v_local
        ax.annotate(f"{v_dist:.4f}  ({delta:+.1f}%)", (1, v_dist), xytext=(10, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=9,
                    color=color, fontweight="bold")

    legend_elems = [
        Line2D([0], [0], color=C_PUSH, marker="o", linewidth=2.4, markersize=7, label="push"),
        Line2D([0], [0], color=C_PULL_HEAD, marker="o", linewidth=2.4, markersize=7, label="pull head"),
        Line2D([0], [0], color=C_PULL_TAIL, marker="o", linewidth=2.4, markersize=7, label="pull tail"),
    ]
    ax.legend(handles=legend_elems, loc="upper center", bbox_to_anchor=(0.2, 1.0),
              frameon=False, fontsize=7)

    ax.set_xlim(-0.75, 1.85)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["LOCAL (1 macchina)", "DIST (3 macchine)"])
    ax.set_ylabel("Throughput (msg/s)")
    ax.set_title("Effetto della distribuzione, per schema", loc="center")
    style_axes(ax)
    savefig(fig, "g07_slope_local_to_dist.png")

# --------------------------------------------------------------------------
# G9 — Guadagno atteso vs osservato (piccoli multipli, una colonna per coppia)
# --------------------------------------------------------------------------
def g09_expected_vs_observed_gain():
    # (etichetta, lavoro delocalizzato %, riduzione wall clock %, delta throughput %)
    rows = [
        ("PUSH\nLOCAL→DIST", 66.7, -204.9, -67.2),
        ("PULL-HEAD\nLOCAL→DIST", 55.7, 41.3, 70.4),
        ("PULL-TAIL\nLOCAL→DIST", 63.6, 39.5, 65.4),
    ]
    labels = ["Lavoro\ndelocalizzato %", "Riduzione\nwall clock %", "Delta\nthroughput %"]
    colors = [C_METRIC_A, C_METRIC_B, C_METRIC_C]

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.6))
    for ax, (title, *vals) in zip(axes, rows):
        bars = ax.bar(range(3), vals, color=colors, edgecolor=INK_PRIMARY, linewidth=0.6, zorder=3)
        bar_labels(ax, bars, fmt="{:+.1f}", dy=1)
        ax.axhline(0, color=BASELINE, linewidth=0.8)
        ax.set_xticks(range(3))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_title(title, fontsize=9.5)
        style_axes(ax)
    axes[0].set_ylabel("%")
    fig.subplots_adjust(top=0.80)
    fig.suptitle("Guadagno atteso (lavoro delocalizzato) vs osservato (wall clock, throughput)",
                 x=0.5, ha="center", y=0.98, fontsize=10)
    fig.text(0.5, -0.04,
              "Se riduzione wall clock ≈ lavoro delocalizzato, il guadagno e' spiegabile col solo\n"
              "spostamento di lavoro fuori dal master, non dallo schema (vedi riserva metodologica).",
              ha="center", fontsize=8.5, color=INK_MUTED, style="italic")
    savefig(fig, "g09_expected_vs_observed_gain.png")

# --------------------------------------------------------------------------
# G12 — Accuracy con barra d'errore
# --------------------------------------------------------------------------
def g12_accuracy_error_bars():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    x = range(len(CONFIGS))
    bars = ax.bar(x, ACCURACY, yerr=ACCURACY_ERR, color=CONFIG_COLORS, width=0.6,
                   edgecolor=INK_PRIMARY, linewidth=0.6, zorder=3,
                   error_kw=dict(ecolor=INK_SECONDARY, elinewidth=1.2, capsize=4))
    for b, a in zip(bars, CONFIG_ALPHA):
        b.set_alpha(a)
    for i, v in enumerate(ACCURACY):
        ax.annotate(f"{v:.1f}%", (i, v + ACCURACY_ERR), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=9, color=INK_SECONDARY)
    ax.axhspan(50 - ACCURACY_ERR, 50 + ACCURACY_ERR, color=INK_MUTED, alpha=0.08, zorder=0)
    ax.set_ylim(0, 70)
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(CONFIG_LABELS, fontsize=9)
    ax.set_title("Accuracy per configurazione (errore standard ≈ ±5 punti, n=100)",
                 loc="center", fontsize=9)
    style_axes(ax)
    fig.text(0.5, -0.1,
              "La fascia grigia (± errore standard attorno al 50%) copre quasi tutti i valori:\n"
              "le differenze tra configurazioni sono compatibili col rumore statistico.",
              ha="center", fontsize=8.5, color=INK_MUTED, style="italic")
    savefig(fig, "g12_accuracy_with_error_bars.png")


# --------------------------------------------------------------------------
# G13 — Wall clock per le 6 configurazioni
# --------------------------------------------------------------------------
def g13_wallclock():
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = range(len(CONFIGS))
    bars = ax.bar(x, WALLCLOCK, color=CONFIG_COLORS, width=0.6,
                   edgecolor=INK_PRIMARY, linewidth=0.6, zorder=3)
    for b, a in zip(bars, CONFIG_ALPHA):
        b.set_alpha(a)
    bar_labels(ax, bars, fmt="{:.0f}s")
    ax.set_ylabel("Wall clock (s)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(CONFIG_LABELS, fontsize=9)
    ax.set_title("Durata complessiva del run", loc="center", fontsize=9)
    style_axes(ax)
    savefig(fig, "g13_wallclock_6config.png")

# --------------------------------------------------------------------------
# G14 — Tempo di servizio t_s per macchina
# --------------------------------------------------------------------------
def g14_ts_per_machine():
    machines = [".12 (master, GPU)", ".5 (worker, GPU)", ".11 (worker, CPU)"]
    ts = [2.1, 2.5, 14.3]
    measured = [True, True, False]  # .11 ricavato dal throughput, non da curl a sistema scarico

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    bars = ax.bar(range(3), ts, color=C_PUSH, width=0.55, edgecolor=INK_PRIMARY,
                  linewidth=0.6, zorder=3)
    bars[2].set_hatch("///")
    bars[2].set_edgecolor(INK_PRIMARY)
    for i, (b, m) in enumerate(zip(bars, measured)):
        note = "" if m else "*"
        ax.annotate(f"{ts[i]:.1f}s{note}", (b.get_x() + b.get_width() / 2, ts[i]),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9.5,
                    color=INK_PRIMARY, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(machines, fontsize=9)
    ax.set_ylabel("Tempo di servizio $t_s$ (s)")
    ax.set_title("Eterogeneita' del cluster: $t_s$ per macchina", loc="center")
    style_axes(ax)
    fig.text(0.5, -0.05,
              "* .11 ricavato dal throughput del run (5 chiamate / throughput / 100 query),\n"
              "non misurato a sistema scarico con curl come le altre due.",
              ha="center", fontsize=8, color=INK_MUTED, style="italic")
    savefig(fig, "g14_ts_per_machine.png")

if __name__ == "__main__":
    g01_throughput()
    g02_e2e_latency()
    g03_e2e_vs_inflight_panels()
    g05_load_stacked_100()
    g06_push_vs_pull_head_dist()
    g07_slope_local_dist()
    g09_expected_vs_observed_gain()
    g12_accuracy_error_bars()
    g13_wallclock()
    g14_ts_per_machine()
    print("\nFatto:", OUT_DIR)
