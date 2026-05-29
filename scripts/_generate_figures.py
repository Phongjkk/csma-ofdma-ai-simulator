"""Tạo các đồ thị cho chương 7 và lưu vào docs/figures/."""
import sys, os
sys.path.insert(0, '.')
os.makedirs('docs/figures', exist_ok=True)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# Style chung
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 150,
    'savefig.bbox': 'tight',
    'savefig.facecolor': 'white',
})

BLUE   = '#2563EB'
RED    = '#DC2626'
GREEN  = '#16A34A'
ORANGE = '#D97706'
PURPLE = '#7C3AED'
GRAY   = '#6B7280'

# ============================================================
# Figure 1: Bianchi Validation
# ============================================================
n_vals    = [5, 10, 20, 30, 50]
bianchi   = [34.367, 32.131, 29.728, 28.238, 26.222]
sim_vals  = [39.289, 37.828, 34.908, 32.570, 29.784]
errors    = [14.3, 17.7, 17.4, 15.3, 13.6]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

ax1.plot(n_vals, bianchi,  'o-', color=BLUE,  lw=2.2, ms=7, label='Bianchi (lý thuyết)')
ax1.plot(n_vals, sim_vals, 's--', color=RED,  lw=2.2, ms=7, label='Mô phỏng')
ax1.fill_between(n_vals, bianchi, sim_vals, alpha=0.10, color=RED)
ax1.set_xlabel('Số STA (n)')
ax1.set_ylabel('Throughput (Mbps)')
ax1.set_title('Đối chiếu Bianchi vs Mô phỏng')
ax1.legend(loc='upper right')
ax1.set_xticks(n_vals)
ax1.grid(axis='y', alpha=0.3)

bars = ax2.bar(n_vals, errors, width=3, color=[BLUE, BLUE, GREEN, GREEN, ORANGE],
               edgecolor='white', linewidth=0.5)
ax2.axhline(y=3, color=RED, linestyle='--', lw=1.5, label='Tiêu chí 3%')
ax2.axhline(y=18, color=GRAY, linestyle=':', lw=1, alpha=0.5)
for bar, err in zip(bars, errors):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{err}%', ha='center', va='bottom', fontsize=9.5)
ax2.set_xlabel('Số STA (n)')
ax2.set_ylabel('Sai số tương đối (%)')
ax2.set_title('Sai số Bianchi vs Mô phỏng')
ax2.legend()
ax2.set_xticks(n_vals)
ax2.set_ylim(0, 25)
ax2.grid(axis='y', alpha=0.3)

plt.suptitle('Hình 7.1 — Kiểm chứng bộ mô phỏng với mô hình Bianchi',
             fontsize=12, y=1.01)
plt.tight_layout()
plt.savefig('docs/figures/fig7_1_bianchi.png')
plt.close()
print('Saved fig7_1_bianchi.png')

# ============================================================
# Figure 2: Performance Table — 5 metrics x 3 loads
# ============================================================
loads     = ['Thấp\n(load=0.2)', 'Trung bình\n(load=0.5)', 'Cao\n(load=2.0)']
thr_vals  = [4.80,  12.30, 34.57]
lat50     = [0.36,   0.37,  1148.0]
lat99     = [0.70,   1.16,  1557.3]
col_pct   = [0.0,    0.5,   44.6]
fair_vals = [0.994,  0.998, 0.999]
util_pct  = [8.9,   22.8,  64.0]
occ_pct   = [8.9,   22.9, 100.0]

fig = plt.figure(figsize=(14, 9))
gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

x = np.arange(len(loads))
bar_kw = dict(width=0.55, edgecolor='white', linewidth=0.6)

# (a) Throughput
ax = fig.add_subplot(gs[0, 0])
bars = ax.bar(x, thr_vals, color=[GREEN, BLUE, RED], **bar_kw)
for b, v in zip(bars, thr_vals):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3, f'{v}', ha='center', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(loads, fontsize=8.5)
ax.set_ylabel('Mbps'); ax.set_title('(a) Throughput')
ax.grid(axis='y', alpha=0.3)

# (b) Latency P50 & P99
ax = fig.add_subplot(gs[0, 1])
ax.bar(x - 0.2, lat50, width=0.35, color=BLUE,  label='P50', **{k:v for k,v in bar_kw.items() if k!='width'})
ax.bar(x + 0.2, lat99, width=0.35, color=RED,   label='P99', **{k:v for k,v in bar_kw.items() if k!='width'})
ax.set_xticks(x); ax.set_xticklabels(loads, fontsize=8.5)
ax.set_ylabel('ms'); ax.set_title('(b) Latency P50 / P99')
ax.legend(fontsize=9)
ax.set_yscale('log')
ax.grid(axis='y', alpha=0.3)

# (c) Collision Rate
ax = fig.add_subplot(gs[0, 2])
bars = ax.bar(x, col_pct, color=[GREEN, BLUE, RED], **bar_kw)
for b, v in zip(bars, col_pct):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3, f'{v}%', ha='center', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(loads, fontsize=8.5)
ax.set_ylabel('%'); ax.set_title('(c) Collision Rate')
ax.grid(axis='y', alpha=0.3)

# (d) Fairness Index
ax = fig.add_subplot(gs[1, 0])
bars = ax.bar(x, fair_vals, color=[GREEN, BLUE, RED], **bar_kw)
for b, v in zip(bars, fair_vals):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.0005, f'{v:.3f}', ha='center', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(loads, fontsize=8.5)
ax.set_ylim(0.98, 1.005)
ax.set_ylabel("Jain's Index"); ax.set_title("(d) Fairness Index")
ax.grid(axis='y', alpha=0.3)

# (e) Util vs Occupancy
ax = fig.add_subplot(gs[1, 1])
ax.bar(x - 0.2, util_pct, width=0.35, color=BLUE,   label='Util (data eff.)', **{k:v for k,v in bar_kw.items() if k!='width'})
ax.bar(x + 0.2, occ_pct, width=0.35, color=ORANGE, label='Occupancy (busy)', **{k:v for k,v in bar_kw.items() if k!='width'})
ax.set_xticks(x); ax.set_xticklabels(loads, fontsize=8.5)
ax.set_ylabel('%'); ax.set_title('(e) Channel Util vs Occupancy')
ax.legend(fontsize=8.5)
ax.set_ylim(0, 115)
ax.axhline(100, color=RED, lw=1, linestyle='--', alpha=0.5)
ax.grid(axis='y', alpha=0.3)

# (f) Summary radar — text version
ax = fig.add_subplot(gs[1, 2])
ax.axis('off')
summary_text = (
    "Summary: load=2.0 (Cao)\n"
    "------------------------\n"
    "Throughput   : 34.57 Mbps\n"
    "Latency P99  : 1 557 ms\n"
    "Collision    : 44.6%\n"
    "Occupancy    : 100% <- bao hoa\n"
    "Dropped      : 5 661 pkts\n"
    "------------------------\n"
    "Offered: 200x20=4000 pkt/s\n"
    "Capacity: ~2857 pkt/s\n"
    "=> He qua tai (rho=1.40)"
)
ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
        va='top', ha='left', fontsize=9.5,
        fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#FEF9C3', edgecolor='#D97706', lw=1.2))
ax.set_title('(f) Phân tích tải cao')

fig.suptitle('Hình 7.2 — Hiệu năng CSMA/CA + OFDMA theo mức tải (n=20 STA)',
             fontsize=12, fontweight='bold', y=1.01)
plt.savefig('docs/figures/fig7_2_performance.png')
plt.close()
print('Saved fig7_2_performance.png')

# ============================================================
# Figure 3: AI Horizon Accuracy
# ============================================================
horizons   = ['1 giây', '3 giây', '5 giây']
mae_vals   = [0.03257, 0.05644, 0.08194]
mape_vals  = [6.23,    9.38,    11.80]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

ax1.plot(horizons, mae_vals, 'o-', color=BLUE, lw=2.2, ms=8)
for i, (h, v) in enumerate(zip(horizons, mae_vals)):
    ax1.annotate(f'{v:.5f}', (h, v), textcoords='offset points',
                 xytext=(0, 9), ha='center', fontsize=9.5)
ax1.set_ylabel('MAE (đơn vị chuẩn hóa)')
ax1.set_title('MAE theo tầm dự đoán')
ax1.set_ylim(0, 0.12)
ax1.grid(axis='y', alpha=0.3)
ax1.fill_between(range(3), mae_vals, alpha=0.12, color=BLUE)

ax2.bar(horizons, mape_vals, color=[GREEN, BLUE, ORANGE], width=0.45,
        edgecolor='white')
for i, (h, v) in enumerate(zip(horizons, mape_vals)):
    ax2.text(i, v + 0.3, f'{v}%', ha='center', fontsize=10)
ax2.axhline(y=20, color=RED, linestyle='--', lw=1.5, label='Ngưỡng chấp nhận 20%')
ax2.set_ylabel('MAPE (%)')
ax2.set_title('MAPE theo tầm dự đoán')
ax2.set_ylim(0, 25)
ax2.legend(fontsize=9)
ax2.grid(axis='y', alpha=0.3)

fig.suptitle('Hình 7.3 — Độ chính xác dự đoán theo tầm dự đoán (Moving Average baseline)',
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('docs/figures/fig7_3_ai_horizon.png')
plt.close()
print('Saved fig7_3_ai_horizon.png')

# ============================================================
# Figure 4: Alert System Confusion Matrix & Metrics
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# Confusion matrix
cm = np.array([[4, 0],   # TP, FN
               [4, 0]])  # FP, TN
im = ax1.imshow(cm, cmap='Blues', vmin=0, vmax=5)
ax1.set_xticks([0, 1]); ax1.set_yticks([0, 1])
ax1.set_xticklabels(['Dự đoán Quá tải', 'Dự đoán Bình thường'], fontsize=10)
ax1.set_yticklabels(['Thực tế\nQuá tải', 'Thực tế\nBình thường'], fontsize=10)
for i in range(2):
    for j in range(2):
        color = 'white' if cm[i,j] > 3 else 'black'
        label = {(0,0):'TP=4',(0,1):'FN=0',(1,0):'FP=4',(1,1):'TN=0'}[(i,j)]
        ax1.text(j, i, label, ha='center', va='center', fontsize=13,
                 fontweight='bold', color=color)
ax1.set_title('Ma trận nhầm lẫn (8 kịch bản)')
plt.colorbar(im, ax=ax1, shrink=0.8)

# Metrics bar
metrics = ['Precision', 'Recall', 'F1-score', 'FPR']
vals    = [0.500, 1.000, 0.667, 1.000]
colors  = [ORANGE, GREEN, BLUE, RED]
bars = ax2.barh(metrics, vals, color=colors, height=0.45, edgecolor='white')
for bar, v in zip(bars, vals):
    ax2.text(v + 0.01, bar.get_y() + bar.get_height()/2,
             f'{v:.3f}', va='center', fontsize=10)
ax2.set_xlim(0, 1.2)
ax2.axvline(x=1.0, color=GRAY, linestyle='--', lw=1, alpha=0.5)
ax2.set_title('Chỉ số đánh giá hệ cảnh báo')
ax2.grid(axis='x', alpha=0.3)

# Annotations
ax2.annotate('Bắt hết quá tải\n(không bỏ sót)',
             xy=(1.0, 1), xytext=(0.7, 1.5),
             fontsize=8.5, color=GREEN,
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.2))
ax2.annotate('Quá nhạy\n(cần hiệu chỉnh ngưỡng)',
             xy=(1.0, 3), xytext=(0.5, 2.5),
             fontsize=8.5, color=RED,
             arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

fig.suptitle('Hình 7.4 — Đánh giá hệ thống cảnh báo sớm quá tải',
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('docs/figures/fig7_4_alert.png')
plt.close()
print('Saved fig7_4_alert.png')

print('\nAll figures saved to docs/figures/')
