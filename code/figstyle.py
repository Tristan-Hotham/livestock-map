"""House style for static figures: fonts (static instances cut from the variable Fraunces font, written to memory),
colours, Natural Earth outlines and the GLW grids drawn in the Equal Earth projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from PIL import Image
from pyproj import Transformer
from common import *

FONTS = "/home/claude/ref/fonts"
FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Regular.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Medium.ttf")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6A6558", "axes.labelcolor": "#22201A",
                     "xtick.color": "#6A6558", "ytick.color": "#6A6558", "svg.fonttype": "none"})
BG, FG, MUT, LAND, RULE, HOT, COOL = "#F7F3E8", "#22201A", "#6A6558", "#E9E1CD", "#E1D8C2", "#9B2D20", "#4E7A3A"
SPC = {k: c for k, _, _, _, c, _ in SPECIES}
SPL = {k: l for k, _, l, _, _, _ in SPECIES}
EXTRA = {"geese": "#7E8C6A", "turkeys": "#A0522D", "asses": "#8A8478", "mules": "#9C8F7A", "camels": "#C9A15E", "camelids": "#B07C9E", "rabbits": "#B7A99A"}
colof = lambda k: SPC.get(k, EXTRA.get(k, "#888888"))
tr = Transformer.from_crs(4326, 8857, always_xy=True)
inv = Transformer.from_crs(8857, 4326, always_xy=True)
NE = jload(f"{PAGE}/world.json")
WORLD_EXT = (-12.6e6, 15.6e6, -6.3e6, 8.4e6)


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in NE["features"]:
    ps = []
    for ring in rings(f["geometry"]):
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        ps.append(np.column_stack([x, y]))
    SHAPES.append((f["properties"]["iso"], ps))


def outlines(ax, fc=LAND, ec="#FFFFFF", lw=.3, z=1, fill=True):
    for iso, ps in SHAPES:
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=fc if fill else "none", ec=ec, lw=lw, zorder=z))


def frame(ax, extent=WORLD_EXT):
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); ax.set_aspect("equal"); ax.axis("off")


# ---------- grids ----------
GRID = {}
FILES = {"a": ["cattle", "sheep", "goats"], "b": ["pigs", "chickens", "buffalo"], "c": ["horses", "ducks", "lsu"], "d": ["dom", "cid", None]}


def grid(k):
    if k not in GRID:
        for f, ks in FILES.items():
            if k in ks:
                a = np.array(Image.open(f"{PAGE}/grid_{f}.png"))
                for i, kk in enumerate(ks):
                    if kk:
                        GRID[kk] = a[:, :, i]
    return GRID[k]


def sample_ee(k, extent=WORLD_EXT, w=2400):
    """Sample a coded grid onto an Equal Earth raster covering extent; returns codes (0 outside)."""
    x0, x1, y0, y1 = extent
    h = int(w * (y1 - y0) / (x1 - x0))
    xs = np.linspace(x0, x1, w); ys = np.linspace(y1, y0, h)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = inv.transform(X, Y)
    ok = np.isfinite(lon) & np.isfinite(lat) & (lat < 85) & (lat > -60) & (np.abs(lon) <= 180)
    r = np.clip(((85 - np.nan_to_num(lat)) * 12).astype(int), 0, 1739)
    c = np.clip(((np.nan_to_num(lon) + 180) * 12).astype(int), 0, 4319)
    a = grid(k)[r, c]
    a[~ok] = 0
    return a


def sample_ll(k, lon0, lon1, lat0, lat1, w=1600, kx=None):
    """Sample a coded grid on a simple lon/lat raster scaled by cos(mid latitude)."""
    kx = kx or np.cos(np.radians((lat0 + lat1) / 2))
    h = int(w * (lat1 - lat0) / ((lon1 - lon0) * kx))
    lon = np.linspace(lon0, lon1, w); lat = np.linspace(lat1, lat0, h)
    LON, LAT = np.meshgrid(lon, lat)
    r = np.clip(((85 - LAT) * 12).astype(int), 0, 1739); c = np.clip(((LON + 180) * 12).astype(int), 0, 4319)
    return grid(k)[r, c]


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def ramp_rgba(codes, colour, pale="#F3EAD0"):
    base, pl = hexrgb(colour), hexrgb(pale)
    dark = base + (np.array([20, 16, 10]) - base) * .55
    t = (codes.astype(float) - 1) / 254
    c = np.where(t[..., None] < .55, pl + (base - pl) * (t[..., None] / .55), base + (dark - base) * ((t[..., None] - .55) / .45))
    a = np.clip(.35 + t * 1.2, 0, 1)
    out = np.dstack([c / 255, a])
    out[codes == 0] = 0
    return out


DOMK = [None] + SKEYS


def dom_rgba(dom, lsu):
    out = np.zeros(dom.shape + (4,))
    for i, k in enumerate(SKEYS):
        m = dom == i + 1
        out[m, :3] = hexrgb(SPC[k]) / 255
    a = np.clip((lsu.astype(float) - 30) / 150, .28, 1)
    out[..., 3] = np.where(dom > 0, a, 0)
    return out


def mix(a, b, t):
    A = hexrgb(a); B = hexrgb(b)
    return "#" + "".join(f"{int(round(x + (y - x) * t)):02x}" for x, y in zip(A, B))


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
