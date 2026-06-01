import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(figsize=(22, 7), dpi=160)
ax.set_xlim(-1.5, 20)
ax.set_ylim(-3, 4.5)
ax.axis('off')

# 配色
colors = {
    'input': '#e5e7eb',
    'enhance': '#bfdbfe',
    'project': '#bfdbfe',
    'fusion': '#bbf7d0',
    'conv': '#fed7aa',
    'fa': '#e9d5ff',
    'pool': '#fecaca',
    'classifier': '#fecaca',
    'label': '#374151',
}

def draw_box(ax, x, y, w, h, color, text, subtext=None, fontsize=10, subfontsize=8):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.03,rounding_size=0.15",
                         facecolor=color, edgecolor='#6b7280', linewidth=1.2)
    ax.add_patch(box)
    ax.text(x, y + 0.08, text, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color=colors['label'])
    if subtext:
        ax.text(x, y - 0.22, subtext, ha='center', va='center',
                fontsize=subfontsize, color='#4b5563')
    return box

def draw_arrow(ax, x1, y1, x2, y2, color='#4b5563'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                               connectionstyle='arc3,rad=0'))

# ===== 主干模块 =====
modules = [
    (0.5, 0, 1.6, 1.0, colors['input'], 'Input', '[N, 15, 50]'),
    (2.3, 0, 1.8, 1.0, colors['enhance'], 'Enhance\n(Temporal Diff)', '[N, 45, 50]\n1st + 2nd order'),
    (4.3, 0, 1.6, 1.0, colors['project'], 'Project', '[N, 15, 50]\n1×1 Conv'),
    (6.3, 0, 2.2, 1.2, colors['fusion'], 'Source Dynamic\nFusion', '[N, 15, 50]\n4-source softmax gating'),
    (8.9, 0, 1.6, 1.0, colors['conv'], 'Conv1', '[N, 15, 50]\nk=7, groups=1'),
    (10.7, 0, 1.5, 1.0, colors['fa'], 'FA Layer', '[N, 15, 50]\nChannel attention'),
    (12.4, 0, 1.5, 1.0, colors['conv'], 'Conv2', '[N, 15, 50]\nk=3'),
    (14.1, 0, 1.5, 1.0, colors['conv'], 'Conv3', '[N, 15, 50]\nk=3'),
    (15.8, 0, 1.5, 1.0, colors['conv'], 'Conv4', '[N, 15, 50]\nk=3'),
    (17.5, 0, 1.5, 1.0, colors['pool'], 'Global\nAvgPool', '[N, 15]'),
    (19.3, 0, 1.6, 1.0, colors['classifier'], 'Classifier', '[N, 4] logits\n15→60→4'),
]

for x, y, w, h, c, t, s in modules:
    draw_box(ax, x, y, w, h, c, t, s)

# 画主干箭头
for i in range(len(modules) - 1):
    x1 = modules[i][0] + modules[i][2] / 2
    x2 = modules[i+1][0] - modules[i+1][2] / 2
    draw_arrow(ax, x1, 0, x2, 0)

# ===== 输入通道语义标注 =====
ax.text(0.5, -1.8, 'odom[0:3]  wheel[3:6]  imu[6:12]  current[12:15]',
        ha='center', va='center', fontsize=9, color='#6b7280',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#f9fafb', edgecolor='#d1d5db'))
ax.annotate('', xy=(0.5, -1.3), xytext=(0.5, -0.55),
            arrowprops=dict(arrowstyle='->', color='#9ca3af', lw=1))

# ===== Enhance 内部分支示意 =====
ax.text(2.3, 1.6, 'diff¹(x): [N,15,49]→pad→[N,15,50]',
        ha='center', va='center', fontsize=8, color='#1e40af',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='#dbeafe', edgecolor='#93c5fd'))
ax.text(2.3, 2.3, 'diff²(x): [N,15,48]→pad→[N,15,50]',
        ha='center', va='center', fontsize=8, color='#1e40af',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='#dbeafe', edgecolor='#93c5fd'))
ax.annotate('', xy=(1.9, 0.55), xytext=(2.0, 1.3),
            arrowprops=dict(arrowstyle='->', color='#60a5fa', lw=1, connectionstyle='arc3,rad=-0.2'))
ax.annotate('', xy=(2.7, 0.55), xytext=(2.6, 1.95),
            arrowprops=dict(arrowstyle='->', color='#60a5fa', lw=1, connectionstyle='arc3,rad=0.2'))

# ===== Source Fusion 内部细节 =====
# 画一个内部小框说明统计量
internal_y = -2.0
ax.text(6.3, internal_y + 0.5, 'Per-source stats:',
        ha='center', va='center', fontsize=9, fontweight='bold', color='#065f46')
ax.text(6.3, internal_y, 'mean_abs  |  std  |  diff_abs',
        ha='center', va='center', fontsize=9, color='#065f46',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ecfdf5', edgecolor='#6ee7b7'))
ax.text(6.3, internal_y - 0.55, '→ scorer FC(3→8→1) → softmax → 4 weights',
        ha='center', va='center', fontsize=9, color='#065f46')
ax.annotate('', xy=(6.3, -0.65), xytext=(6.3, internal_y + 0.85),
            arrowprops=dict(arrowstyle='->', color='#34d399', lw=1.2))

# ===== FA Layer 内部细节 =====
ax.text(10.7, 1.55, 'avg_pool → FC(15→8→15) → sigmoid\nenhance = (attn + pooled) · x',
        ha='center', va='center', fontsize=8, color='#6b21a8',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='#f3e8ff', edgecolor='#d8b4fe'))
ax.annotate('', xy=(10.7, 0.55), xytext=(10.7, 1.15),
            arrowprops=dict(arrowstyle='->', color='#c084fc', lw=1))

# ===== 图例 =====
legend_items = [
    (colors['enhance'], 'Temporal Difference'),
    (colors['project'], 'Projection'),
    (colors['fusion'], 'Source Dynamic Fusion'),
    (colors['conv'], 'Conv1d Block'),
    (colors['fa'], 'FA Recalibration'),
    (colors['pool'], 'Pooling / Classifier'),
]
legend_x = 15.5
legend_y = 3.3
ax.text(legend_x - 0.3, legend_y + 0.4, 'Module Types',
        ha='left', va='center', fontsize=10, fontweight='bold', color='#374151')
for i, (c, label) in enumerate(legend_items):
    yy = legend_y - i * 0.45
    rect = mpatches.Rectangle((legend_x - 0.3, yy - 0.12), 0.35, 0.24,
                               facecolor=c, edgecolor='#6b7280', linewidth=0.8)
    ax.add_patch(rect)
    ax.text(legend_x + 0.15, yy, label, ha='left', va='center',
            fontsize=9, color='#4b5563')

# 标题
ax.text(9.5, 4.0, 'SAGE-CNN Architecture  (Source-Aware Gradient-Enhanced CNN)',
        ha='center', va='center', fontsize=16, fontweight='bold', color='#111827')

plt.tight_layout()
plt.savefig('ypmodel/sage_cnn_architecture.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('Saved to ypmodel/sage_cnn_architecture.png')
