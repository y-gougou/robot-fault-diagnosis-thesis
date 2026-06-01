import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ablation_bar_chart.png"

models = ["SAGE-CNN", "w/o SAF", "w/o Diff", "w/o Diff+SAF"]
accuracy = [0.9803, 0.9807, 0.9691, 0.9658]
macro_f1 = [0.9647, 0.9646, 0.9409, 0.9301]

x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5.2), dpi=180)

bars_acc = ax.bar(x - width / 2, accuracy, width, label="Accuracy",
                  color="#5a8f5a", edgecolor="#27313a", linewidth=0.6)
bars_f1 = ax.bar(x + width / 2, macro_f1, width, label="Macro F1",
                 color="#326f9b", edgecolor="#27313a", linewidth=0.6)

ax.set_ylabel("Score")
ax.set_title("Ablation Study Results")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0.90, 1.0)
ax.grid(axis="y", alpha=0.25)
ax.tick_params(axis="x", rotation=15)
ax.legend(loc="upper right")

# annotate bars
for bar, val in zip(bars_acc, accuracy):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.003,
            f"{val*100:.2f}%", ha="center", va="bottom", fontsize=8)

for bar, val in zip(bars_f1, macro_f1):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.003,
            f"{val*100:.2f}%", ha="center", va="bottom", fontsize=8)

# draw a subtle horizontal line at the top (SAGE-CNN macro f1) for reference
ax.axhline(y=macro_f1[0], color="#326f9b", linestyle="--", linewidth=0.6, alpha=0.4)

fig.tight_layout()
fig.savefig(OUT)
plt.close(fig)
print(f"Saved ablation bar chart to: {OUT}")
