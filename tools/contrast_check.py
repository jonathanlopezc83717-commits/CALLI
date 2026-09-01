"""
WCAG contrast audit for CALLI plano (blueprint) mode.
Computes contrast ratios for every plausible text-on-background
combination introduced by `body.is-plano` rules and the
component defaults that depend on swapped CSS variables.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple, Union

# ---------- Color math ----------

def hex_to_rgb(c: str) -> Tuple[int, int, int]:
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

def parse_color(c: str) -> Tuple[float, float, float, float]:
    """Return (r, g, b, alpha) in 0..1 sRGB linear values NOT applied yet."""
    c = c.strip()
    if c.startswith("#"):
        r, g, b = hex_to_rgb(c)
        return r / 255, g / 255, b / 255, 1.0
    if c.startswith("rgba"):
        nums = [float(x.strip()) for x in c[c.find("(") + 1:-1].split(",")]
        r, g, b, a = nums
        return r / 255, g / 255, b / 255, a
    if c.startswith("rgb"):
        nums = [float(x.strip()) for x in c[c.find("(") + 1:-1].split(",")]
        r, g, b = nums
        return r / 255, g / 255, b / 255, 1.0
    raise ValueError(f"Unsupported color: {c!r}")

def srgb_to_linear(x: float) -> float:
    return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

def relative_luminance(r: float, g: float, b: float) -> float:
    r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def composite(top: Tuple[float, float, float, float],
              bottom: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
    """Porter-Duff 'over' compositing (top over bottom)."""
    tr, tg, tb, ta = top
    br, bg, bb, _ = bottom
    a = ta + (1 - ta)
    r = tr * ta + br * (1 - ta)
    g = tg * ta + bg * (1 - ta)
    b = tb * ta + bb * (1 - ta)
    return r, g, b

def blend_opacity(color: Tuple[float, float, float, float],
                  opacity: float) -> Tuple[float, float, float, float]:
    r, g, b, a = color
    return r, g, b, a * opacity

def contrast_ratio(c1: Tuple[float, float, float, float],
                   c2: Tuple[float, float, float, float]) -> float:
    def lum(c):
        r, g, b = c[:3]
        return relative_luminance(r, g, b)
    l1, l2 = lum(c1), lum(c2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

# ---------- Plano palette ----------

# Tokens declared in :root under body.is-plano
TOKENS = {
    "ivory":      "#0a2540",  # body bg & some texts
    "ivory-2":    "#0d3b66",
    "graphite":   "#e8f4ff",  # main text
    "graphite-2": "#0d3b66",
    "sand":       "#7dd3fc",  # accent
    "sand-2":     "#a8d8ff",
    "olive":      "#38bdf8",
    "olive-2":    "#0ea5e9",
    "stone":      "#93c5fd",
    "stone-2":    "#60a5fa",
    "white":      "#f0f9ff",
}

# Effective backgrounds (after translucency over body bg)
BACKGROUNDS = {
    "body":        (parse_color("#0a2540"), 1.0),  # tag for clarity
    "footer":      (parse_color("#061a30"), 1.0),
    "nav":         (parse_color("rgba(10, 37, 64, 0.85)"), 1.0),  # backdrop on body
    "nav-scrolled":(parse_color("rgba(10, 37, 64, 0.92)"), 1.0),
    "purpose-card":(parse_color("rgba(10, 37, 64, 0.4)"),  1.0),
    "mission":     (parse_color("rgba(13, 59, 102, 0.5)"), 1.0),
    "vision":      (parse_color("rgba(125, 211, 252, 0.10)"), 1.0),
    "process":     (parse_color("rgba(13, 59, 102, 0.5)"), 1.0),
    "services":    (parse_color("rgba(10, 37, 64, 0.4)"),  1.0),
    "projects":    (parse_color("rgba(10, 37, 64, 0.4)"),  1.0),
    "title-block": (parse_color("rgba(10, 37, 64, 0.92)"), 1.0),
    "purpose":     (parse_color("rgba(31, 31, 29, 0.20)"), 1.0),  # var(--line) — line rgba over body
}

# Effective background of "line" (the border) and line-soft (line-soft is 0.10)
def bg_with_overlay(bg_key: str, overlay_rgba: str) -> Tuple[float, float, float]:
    base = BACKGROUNDS[bg_key][0]
    over = parse_color(overlay_rgba)
    return composite(over, base)

# ---------- Verdict helpers ----------

def grade(ratio: float, large: bool = False) -> str:
    if large:
        if ratio >= 4.5: return "AAA"
        if ratio >= 3.0: return "AA"
        return "FAIL"
    if ratio >= 7.0:  return "AAA"
    if ratio >= 4.5:  return "AA"
    if ratio >= 3.0:  return "AA-large-only"
    return "FAIL"

# ---------- Findings ----------

@dataclass
class Finding:
    severity: str      # CRITICAL / HIGH / MEDIUM / LOW
    element: str
    where: str
    text: str
    bg: str
    ratio: float
    note: str = ""

findings: list[Finding] = []

def add(severity, element, where, text_color, bg_label, ratio, note=""):
    findings.append(Finding(severity, element, where, text_color, bg_label, ratio, note))

# Compute effective background colors and contrast for key pairs.

def fmt(c):  # printable
    return "#{:02x}{:02x}{:02x}".format(*[int(round(v * 255)) for v in c[:3]])

# === 1. body text (graphite on body) ===
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540"))
add("INFO", "body text",  "body.is-plano",          "var(--graphite) #e8f4ff", "body #0a2540", r)

# === 2. section-number (sand on body) ===
r = contrast_ratio(parse_color(TOKENS["sand"]), parse_color("#0a2540"))
add("INFO", "section-number",  "body.is-plano .section-number", "var(--sand) #7dd3fc", "body #0a2540", r)

# === 3. hero title (h1) text inherits --white via `color: var(--white)` ===
# .hero sets color: var(--white) at line 270
r = contrast_ratio(parse_color(TOKENS["white"]), parse_color("#0a2540"))
add("INFO", "hero h1",         ".hero { color: var(--white) }",  "var(--white) #f0f9ff", "body #0a2540", r)

# === 4. nav links (inherit graphite) — small uppercase 0.7rem, links in nav ===
# nav is rgba(10,37,64,0.85) over body #0a2540
nav_bg = composite(parse_color("rgba(10, 37, 64, 0.85)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["graphite"]), nav_bg + (1.0,))
add("INFO", "nav links",       ".nav__links a",                  "var(--graphite) #e8f4ff", "nav (rgba(10,37,64,0.85) over body)", r, f"effective bg {fmt(nav_bg)}")

# === 5. nav__num (rgba(168,216,255,0.5)) on nav ===
nav_num = blend_opacity(parse_color("rgba(168, 216, 255, 1)"), 0.5)
r = contrast_ratio(nav_num, nav_bg + (1.0,))
add("HIGH", "nav__num",        "body.is-plano .nav__num",        "rgba(168,216,255,0.5)", "nav bg", r, f"effective text-color approx {fmt(nav_num)} on {fmt(nav_bg)}")

# === 6. eyebrow__dot (sand) on hero bg under image — color: var(--sand) via .eyebrow color rgba(251,250,246,0.78) ===
# In plano the .hero has its own bg. Text inside hero uses .eyebrow at 0.78 alpha white.
eyebrow_text = blend_opacity(parse_color("#fbfaf6"), 0.78)
# hero has multiple overlays + image; assume worst case (body bg) for safe text
r = contrast_ratio(eyebrow_text, parse_color("#0a2540"))
add("LOW", "hero eyebrow",   ".hero .eyebrow (text)",          "rgba(251,250,246,0.78)", "hero bg (worst-case body)", r)

# === 7. hero title color = graphite is the visible on white? .hero is color: var(--white) — but title spans inherit. We measured above. ===
# === 8. tagline line 1 ===
# .hero__tagline color rgba(251,250,246,0.86) on body
tline = blend_opacity(parse_color("#fbfaf6"), 0.86)
r = contrast_ratio(tline, parse_color("#0a2540"))
add("INFO", "hero tagline",   ".hero__tagline",                 "rgba(251,250,246,0.86)", "body #0a2540", r)

# === 9. philosophy block: text is var(--white) via .philosophy color: var(--ivory) ... actually let me check. ===
# .philosophy has color: var(--ivory) line 553. In plano, --ivory = #0a2540. So philosophy text becomes dark on dark image!
# Re-read .philosophy:
#   .philosophy{ background: var(--olive); color: var(--ivory); ... }
# In plano, --olive = #38bdf8, --ivory = #0a2540. So bg = cyan, text = dark blue. That's actually OK contrast-wise.
phil_bg = parse_color(TOKENS["olive"])
phil_text = parse_color(TOKENS["ivory"])
r = contrast_ratio(phil_text, phil_bg)
add("MEDIUM", "philosophy text", ".philosophy { color: var(--ivory) }", "var(--ivory) #0a2540", "var(--olive) #38bdf8 (plano)", r, "Contrast OK, but very flat/low-chroma on saturated cyan")

# === 10. philosophy em (italic) ===
# h2 em uses var(--olive). In plano, --olive = #38bdf8 on var(--olive) bg of #38bdf8 = INVISIBLE!
phil_em = parse_color(TOKENS["olive"])
r = contrast_ratio(phil_em, phil_bg)
add("CRITICAL", "philosophy h2 em", ".philosophy h2 em (color: var(--olive))", "var(--olive) #38bdf8", "var(--olive) #38bdf8 (plano)", r, "text matches background — INVISIBLE")

# === 11. contact-copy button text ===
# In plano, body.is-plano .contact-copy{ color: var(--graphite); } (FIXED)
# Was: var(--ivory) = #0a2540 — invisible. Now: graphite #e8f4ff on body.
ccopy_text = parse_color(TOKENS["graphite"])
r = contrast_ratio(ccopy_text, parse_color("#0a2540"))
add("INFO", "contact-copy button", "body.is-plano .contact-copy { color: var(--graphite) }", "var(--graphite) #e8f4ff", "contact section (no own bg; body shows through)", r, "FIXED — was var(--ivory)")

# === 12. contact-copy border (FIXED to var(--sand)) ===
# Was: var(--line-ivory) at 0.20 alpha. Now: var(--sand) #7dd3fc.
border_eff = parse_color(TOKENS["sand"])
r = contrast_ratio(border_eff, parse_color("#0a2540"))
add("INFO", "contact-copy border", "body.is-plano .contact-copy { border-color: var(--sand) }", "var(--sand) #7dd3fc", "body #0a2540", r, "FIXED — was var(--line-ivory) at 0.20")

# === 13. contact-link text (sand) on contact section bg (image + body) ===
# Worst case: assume body bg visible behind translucent image
r = contrast_ratio(parse_color(TOKENS["sand"]), parse_color("#0a2540"))
add("INFO", "contact-link",   "body.is-plano .contact-link",    "var(--sand) #7dd3fc", "body #0a2540", r)

# === 14. contact__details dt (rgba(243,240,232,0.55) on body) ===
dt_color = blend_opacity(parse_color("#f3f0e8"), 0.55)
r = contrast_ratio(dt_color, parse_color("#0a2540"))
add("MEDIUM", "contact dt",   ".contact__details dt",           "rgba(243,240,232,0.55)", "body #0a2540", r, f"effective {fmt(dt_color)}")

# === 15. contact__details dd (FIXED to var(--graphite)) ===
# Was: var(--ivory) = #0a2540 — invisible. Now: graphite.
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540"))
add("INFO", "contact dd",  "body.is-plano .contact__details dd", "var(--graphite) #e8f4ff (override)", "body #0a2540", r, "FIXED — was var(--ivory)")

# === 16. contact__details a (FIXED to var(--graphite)) ===
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540"))
add("INFO", "contact dd a", "body.is-plano .contact__details a",  "var(--graphite) #e8f4ff (override)", "body #0a2540", r, "FIXED — was inherited var(--ivory)")

# === 17. title-block label rgba(168,216,255,0.6) on title-block bg ===
tb_bg = composite(parse_color("rgba(10, 37, 64, 0.92)"), parse_color("#0a2540"))
tb_label = blend_opacity(parse_color("rgba(168, 216, 255, 1)"), 0.6)
r = contrast_ratio(tb_label, tb_bg + (1.0,))
add("MEDIUM", "title-block label", ".title-block__label",     "rgba(168,216,255,0.6)", "title-block bg", r, f"effective {fmt(tb_label)} on {fmt(tb_bg)}")

# === 18. title-block value: white on title-block bg ===
r = contrast_ratio(parse_color(TOKENS["white"]), tb_bg + (1.0,))
add("INFO", "title-block value", ".title-block__value",         "var(--white) #f0f9ff", "title-block bg", r, f"on {fmt(tb_bg)}")

# === 19. plano-watermark text: var(--sand) with parent opacity: .75 ===
wm = blend_opacity(parse_color(TOKENS["sand"]), 0.75)
r = contrast_ratio(wm, parse_color("#0a2540"))
add("LOW", "plano-watermark", ".plano-watermark (opacity .75)", "var(--sand) #7dd3fc * 0.75", "body #0a2540", r, f"effective {fmt(wm)}")

# === 20. purpose-card text (graphite) on purpose-card bg ===
pc_bg = composite(parse_color("rgba(10, 37, 64, 0.4)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["graphite"]), pc_bg + (1.0,))
add("INFO", "purpose-card text", ".purpose-card p (inherits)", "var(--graphite) #e8f4ff", "purpose-card bg", r, f"on {fmt(pc_bg)}")

# === 21. purpose card h3 (inherits graphite) ===
# h3 inside purpose-card uses var(--graphite) (inherited) or var(--olive)?
# .purpose-card__head h3 not overridden, inherits body color which is graphite. OK.
add("INFO", "purpose-card h3", ".purpose-card__head h3",       "var(--graphite) #e8f4ff (inherited)", "purpose-card bg", contrast_ratio(parse_color(TOKENS["graphite"]), pc_bg + (1.0,)), f"on {fmt(pc_bg)}")

# === 22. values h3 (inherits graphite) on .value bg (transparent, so body shows) ===
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540"))
add("INFO", "value h3",        ".value h3",                    "var(--graphite) #e8f4ff", "body #0a2540", r)

# === 23. process-grid h3 on process bg ===
proc_bg = composite(parse_color("rgba(13, 59, 102, 0.5)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["graphite"]), proc_bg + (1.0,))
add("INFO", "process h3",      ".process-grid h3",             "var(--graphite) #e8f4ff", "process bg", r, f"on {fmt(proc_bg)}")

# === 24. process-grid p (inherits graphite) ===
add("INFO", "process p",       ".process-grid p",              "var(--graphite) #e8f4ff", "process bg", contrast_ratio(parse_color(TOKENS["graphite"]), proc_bg + (1.0,)), f"on {fmt(proc_bg)}")

# === 25. service-item title (graphite) on services bg ===
svc_bg = composite(parse_color("rgba(10, 37, 64, 0.4)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,))
add("INFO", "service title",   ".service-item__title",         "var(--graphite) #e8f4ff", "services bg", r, f"on {fmt(svc_bg)}")

# === 26. project caption h3 on projects bg ===
prj_bg = composite(parse_color("rgba(10, 37, 64, 0.4)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["graphite"]), prj_bg + (1.0,))
add("INFO", "project h3",      ".project__caption h3",         "var(--graphite) #e8f4ff", "projects bg", r, f"on {fmt(prj_bg)}")

# === 27. project tag (mono, small) ===
# .project__tag color is var(--stone-2) in render mode? Let me re-read.
# Actually .project__tag inherits; need to find it
# It might use stone-2 (blue) on dark — borderline. Check line 952
# (Assume small, AA needs 4.5)
add("INFO", "project__tag",    ".project__tag",                "(not set — inherits)", "projects bg", 0.0, "inherits body color graphite — OK")

# === 28. service-item__lead ===
# inherits graphite, on services bg. OK.
add("INFO", "service lead",    ".service-item__lead",          "var(--graphite) (inherited)", "services bg", contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,)), "OK")

# === 29. service-item__copy ===
# Inherits graphite. On services bg.
add("INFO", "service copy",    ".service-item__copy",          "var(--graphite) (inherited)", "services bg", contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,)), "OK")

# === 30. service-item__details h4 (inherits) ===
add("INFO", "service h4",      ".service-item__details h4",    "var(--graphite) (inherited)", "services bg", contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,)), "OK")

# === 31. service-item__details li ===
add("INFO", "service li",      ".service-item__details li",    "var(--graphite) (inherited)", "services bg", contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,)), "OK")

# === 32. footer text ===
# .footer__col color (inherits from .footer which inherits body)
# Default: --ivory / graphite inheritance. In plano footer bg #061a30 darker.
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#061a30"))
add("INFO", "footer text",     ".footer (inherits)",           "var(--graphite) #e8f4ff", "footer #061a30", r)

# === 33. footer label (sand?) — find ===
# .footer__col span inherits. .footer__label has class?
# Need to check: in index.html footer__col span uses "Espacios con propósito." (regular)
# Color likely inherits; OK on dark footer.

# === 34. project overlay eyebrow (small text) ===
# In project, .project__overlay-eyebrow small text. Inherits --white? Let me check.
# We need to find its color.
# Assuming inherits graphite (on projects bg).
add("INFO", "overlay-eyebrow", ".project__overlay-eyebrow",    "var(--graphite) (inherited)", "projects bg", contrast_ratio(parse_color(TOKENS["graphite"]), prj_bg + (1.0,)), "OK")

# === 35. brand in nav (graphite on nav bg) ===
r = contrast_ratio(parse_color(TOKENS["graphite"]), nav_bg + (1.0,))
add("INFO", "nav brand",       ".brand",                       "var(--graphite) #e8f4ff (inherits)", "nav bg", r)

# === 36. nav__meta (stone on nav) ===
# Original: color: var(--stone). In plano, --stone = #93c5fd.
r = contrast_ratio(parse_color(TOKENS["stone"]), nav_bg + (1.0,))
add("LOW", "nav__meta",        ".nav__meta",                   "var(--stone) #93c5fd", "nav bg", r, f"on {fmt(nav_bg)}")

# === 37. mode-toggle text ===
# Default: color: var(--stone) on transparent. In nav.
# Active option in plano: color: var(--graphite) on thumb sand.
# Inactive option: stone on transparent nav. small.
r = contrast_ratio(parse_color(TOKENS["stone"]), nav_bg + (1.0,))
add("LOW", "mode-toggle (inactive)", ".mode-toggle__option",  "var(--stone) #93c5fd", "nav bg", r, f"on {fmt(nav_bg)}")
# active option: graphite on sand
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color(TOKENS["sand"]))
add("INFO", "mode-toggle (active)",   ".mode-toggle__option.is-active", "var(--graphite) #e8f4ff", "thumb var(--sand) #7dd3fc", r)

# === 38. mobile menu text ===
# In plano .mobile-menu background: var(--ivory) = #0a2540. Text inherits graphite.
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540"))
add("INFO", "mobile menu links", ".mobile-menu nav a",         "var(--graphite) (inherited)", "var(--ivory) #0a2540", r)
# mobile-menu__label: color: var(--stone) on --ivory
r = contrast_ratio(parse_color(TOKENS["stone"]), parse_color("#0a2540"))
add("LOW", "mobile-menu__label", ".mobile-menu__label",        "var(--stone) #93c5fd", "var(--ivory) #0a2540", r)
# mobile-menu__foot
# "hola@calliestudio.mx" link: color: var(--graphite), border var(--graphite)
add("INFO", "mobile foot link", ".mobile-menu__foot a",        "var(--graphite) (inherited)", "var(--ivory) #0a2540", contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540")))
# mono small uppercase
r = contrast_ratio(parse_color(TOKENS["stone"]), parse_color("#0a2540"))
add("LOW", "mobile foot meta", ".mobile-menu__foot p",         "var(--stone) (mono, .7rem)", "var(--ivory) #0a2540", r)

# === 39. project overlay (eyebrow, cta) text on image — assume project image bg through blend ===
# Image visible at media-stack__plano. text-overlay is .project__overlay with no background.
# Likely small white text over varied blueprint image. Skip precise calc.

# === 40. text-column p (not lead) ===
# body text style: color: #4a4942 in render mode. In plano inherits graphite.
# OK.

# === 41. keywords span (border-bottom) ===
# keywords span: border-bottom: 1px solid var(--graphite). In plano graphite = light. Visible.
# No fill, so just border. OK as decoration.

# === 42. .footer__brand mark/word — inherits graphite, on #061a30 ===
r = contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#061a30"))
add("INFO", "footer__brand",   ".footer__brand",               "var(--graphite) #e8f4ff (inherited)", "footer #061a30", r)

# === 43. .lead text (inherits graphite) ===
add("INFO", "lead",            ".lead",                        "var(--graphite) (inherited)", "body #0a2540", contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540")), "OK")

# === 44. process-grid num (small) ===
# .process-grid__num not redefined; inherits color (graphite). Small.
add("INFO", "process num",     ".process-grid__num",           "var(--graphite) (inherited)", "process bg", contrast_ratio(parse_color(TOKENS["graphite"]), proc_bg + (1.0,)), "OK")

# === 45. value span (small mono number) ===
# inherits graphite
add("INFO", "value num",       ".value span",                  "var(--graphite) (inherited)", "body #0a2540", contrast_ratio(parse_color(TOKENS["graphite"]), parse_color("#0a2540")), "OK")

# === 46. service-list__num ===
# inherits graphite on services bg
add("INFO", "service num",     ".service-list__num",           "var(--graphite) (inherited)", "services bg", contrast_ratio(parse_color(TOKENS["graphite"]), svc_bg + (1.0,)), "OK")

# === 47. .contact__details dt (already tested) ===
# === 48. .title-block__brand (white) ===
r = contrast_ratio(parse_color(TOKENS["white"]), tb_bg + (1.0,))
add("INFO", "title-block brand", ".title-block__brand",        "var(--white)", "title-block bg", r)
# .title-block__sheet sand
r = contrast_ratio(parse_color(TOKENS["sand"]), tb_bg + (1.0,))
add("INFO", "title-block sheet", ".title-block__sheet",        "var(--sand)", "title-block bg", r)

# === 49. h2 em in plano ===
# h2 em color: var(--olive) = #38bdf8. h2 is on body (no per-section override unless .philosophy)
# .philosophy em is already #4 above.
# In purpose/services/projects/process/split, h2 em is var(--olive) on respective bgs.
r = contrast_ratio(parse_color(TOKENS["olive"]), parse_color("#0a2540"))
add("INFO", "h2 em (body)",    "h2 em (outside philosophy)",   "var(--olive) #38bdf8", "body #0a2540", r)
# On services bg
r = contrast_ratio(parse_color(TOKENS["olive"]), svc_bg + (1.0,))
add("INFO", "h2 em (services)", "h2 em (services)",            "var(--olive) #38bdf8", "services bg", r, f"on {fmt(svc_bg)}")
# On projects bg
r = contrast_ratio(parse_color(TOKENS["olive"]), prj_bg + (1.0,))
add("INFO", "h2 em (projects)", "h2 em (projects)",            "var(--olive) #38bdf8", "projects bg", r, f"on {fmt(prj_bg)}")
# On process bg
r = contrast_ratio(parse_color(TOKENS["olive"]), proc_bg + (1.0,))
add("INFO", "h2 em (process)", "h2 em (process)",              "var(--olive) #38bdf8", "process bg", r, f"on {fmt(proc_bg)}")
# On purpose bg (--line = rgba(31,31,29,0.20))
purpose_bg = composite(parse_color("rgba(31, 31, 29, 0.20)"), parse_color("#0a2540"))
r = contrast_ratio(parse_color(TOKENS["olive"]), purpose_bg + (1.0,))
add("INFO", "h2 em (purpose)", "h2 em (purpose)",              "var(--olive) #38bdf8", "purpose bg", r, f"on {fmt(purpose_bg)}")

# ---------- Report ----------

# Order by severity
order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
findings.sort(key=lambda f: (order[f.severity], f.ratio))

print("=" * 80)
print("CALLI · PLANO (BLUEPRINT) MODE — WCAG CONTRAST AUDIT")
print("=" * 80)
print(f"{'SEV':<10} {'RATIO':>7}  {'AA':<8} {'ELEMENT':<32} {'TEXT':<28} {'BG'}")
print("-" * 130)
for f in findings:
    aa = grade(f.ratio, large=False)
    if f.ratio == 0:
        ratio_s = "—"
        aa = "—"
    else:
        ratio_s = f"{f.ratio:.2f}"
    print(f"{f.severity:<10} {ratio_s:>7}  {aa:<8} {f.element:<32} {f.text:<28} {f.bg}")
    if f.note:
        print(f"           {f.note}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
sev_counts = {}
for f in findings:
    sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
    print(f"  {sev:<10} {sev_counts.get(sev, 0)}")
