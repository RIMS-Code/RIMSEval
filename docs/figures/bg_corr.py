"""Create a schematic figure for Background Correction explanation."""

import matplotlib.pyplot as plt
import numpy as np

channels = np.arange(0, 1, 0.001)

# background
bg = np.random.rand(len(channels))

# a peak at 0.5
pk_rnd = np.random.randn(100000)
pk, _, _ = plt.hist(pk_rnd, bins=len(channels))
pk /= np.max(pk) / 10

# signal
signal = pk + bg

# areas to mark
bg_shades = [[0.05, 0.15], [0.85, 0.95]]
pk_shade = 0.25, 0.75

# plot
fig, ax = plt.subplots(1, 1)
fig.set_size_inches(4, 3)

ax.fill_between(
    channels, signal, np.zeros_like(channels), color="tab:blue", linewidth=0
)

# mark bg
bgcol = "tab:orange"
for it, lims in enumerate(bg_shades):  # areas must be in limits
    lim1 = np.where(channels >= lims[0])[0][0]
    lim2 = np.where(channels >= lims[1])[0][0]
    ax.fill_between(
        channels[lim1:lim2],
        signal[lim1:lim2],
        np.zeros_like(channels[lim1:lim2]),
        color=bgcol,
        linewidth=0,
    )
    ax.text(
        channels[lim2 - int((lim2 - lim1) / 2)],
        1.3,
        f"$B_{{{it+1}}}$",
        ha="center",
        va="bottom",
    )

# mark peak
lim1 = np.where(channels >= pk_shade[0])[0][0]
lim2 = np.where(channels >= pk_shade[1])[0][0]
ax.fill_between(
    channels[lim1:lim2],
    signal[lim1:lim2],
    np.zeros_like(channels[lim1:lim2]),
    color="tab:green",
    linewidth=0,
)
ax.text(0.6, 9, "$A_{p}$")

# remove ticks and markers
ax.xaxis.set_tick_params(labelbottom=False)
ax.yaxis.set_tick_params(labelleft=False)
ax.set_xticks([])
ax.set_yticks([])

# labels
ax.set_xlabel("Channel")
ax.set_ylabel("Signal")

fig.tight_layout()

# fig.show()
fig.savefig("bg_corr.png", dpi=300)
