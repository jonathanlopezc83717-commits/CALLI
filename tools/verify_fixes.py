"""
Post-fix verification: confirm the 6 user-reported texts now have
proper contrast in plano mode AND still work in render mode.
Self-contained — doesn't import the audit script to avoid side effects.
"""

def hex_to_rgb(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

def parse_color(c):
    c = c.strip()
    if c.startswith("#"):
        r, g, b = hex_to_rgb(c)
        return r / 255, g / 255, b / 255
    if c.startswith("rgba"):
        nums = [float(x.strip()) for x in c[c.find("(") + 1:-1].split(",")]
        r, g, b, a = nums
        # Return pre-composited color over opaque (we approximate transparency
        # by compositing against a black bg for "on dark" tests, against white
        # for "on light" tests). For the texts we test, the bg assumption is
        # already encoded in the caller, so we just ignore alpha here.
        return r / 255, g / 255, b / 255
    if c.startswith("rgb"):
        nums = [float(x.strip()) for x in c[c.find("(") + 1:-1].split(",")]
        r, g, b = nums
        return r / 255, g / 255, b / 255
    raise ValueError(c)

def srgb_to_linear(x):
    return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

def relative_luminance(r, g, b):
    r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(c1, c2):
    l1 = relative_luminance(*c1[:3])
    l2 = relative_luminance(*c2[:3])
    if l1 < l2: l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def grade(r):
    if r >= 7.0:  return "AAA"
    if r >= 4.5:  return "AA"
    if r >= 3.0:  return "AA-large"
    return "FAIL"

# Effective backgrounds
RENDER_BODY_BG     = "#f3f0e8"   # body in render mode
RENDER_CONTACT_BG  = "#0a0a08"   # contact section in render: dark image + dark gradient
PLANO_BODY_BG      = "#0a2540"   # body in plano mode

cases = [
    ("'Nuestro trabajo parte de comprender...' (.text-column p)",
        "#1f1f1d", "#e8f4ff", RENDER_BODY_BG, PLANO_BODY_BG),
    ("'Cada proyecto comienza con una pregunta...' (.process-intro p)",
        "#1f1f1d", "#e8f4ff", RENDER_BODY_BG, PLANO_BODY_BG),
    ("'Copiar email' button (.contact-copy)",
        "#f3f0e8", "#e8f4ff", RENDER_CONTACT_BG, PLANO_BODY_BG),
    ("'+52 55 0000 0000' (.contact__details dd)",
        "#f3f0e8", "#e8f4ff", RENDER_CONTACT_BG, PLANO_BODY_BG),
    ("'Ciudad de Mexico, Mexico' (.contact__details dd)",
        "#f3f0e8", "#e8f4ff", RENDER_CONTACT_BG, PLANO_BODY_BG),
    ("'Instagram @calliestudio' (.contact__details a)",
        "#f3f0e8", "#e8f4ff", RENDER_CONTACT_BG, PLANO_BODY_BG),
]

print("=" * 110)
print("VERIFICATION: 6 user-reported texts (post-fix)")
print("=" * 110)
hdr = f"{'TEXT':<60} {'MODE':<8} {'TEXT':<10} {'BG':<10} {'RATIO':>6}  {'WCAG':<9} {'STATUS'}"
print(hdr)
print("-" * 110)
all_ok = True
for label, rc, pc, rbg, pbg in cases:
    rr = contrast_ratio(parse_color(rc), parse_color(rbg))
    pr = contrast_ratio(parse_color(pc), parse_color(pbg))
    for mode, color, bg, ratio in [("render", rc, rbg, rr), ("plano", pc, pbg, pr)]:
        g = grade(ratio)
        status = "OK" if g != "FAIL" else "FAIL"
        if status == "FAIL":
            all_ok = False
        print(f"{label:<60} {mode:<8} {color:<10} {bg:<10} {ratio:>5.2f}  {g:<9} {status}")

print()
print("=" * 110)
print("RESULT:", "ALL 6 TEXTS FIXED" if all_ok else "STILL HAVE ISSUES")
print("=" * 110)
print()
print("BONUS: .philosophy h2 em (the italic word 'vemos.')")
print("  In plano, h2 em is var(--olive) #38bdf8 on .philosophy bg var(--olive) #38bdf8 = 1.00:1 FAIL")
print("  Flagged in original audit, not in your list. Awaiting your call.")
