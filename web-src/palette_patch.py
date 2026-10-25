"""Palet kuning GC-Ex (0.7.0): kuning lemon jenuh #f5c400 diganti emas seimbang yang komplementer tepat dengan navy #233a7e
(OKLCH hue 86.5° = hue navy 266.5° + 180°, chroma 0.145, L 0.83). Teks navy di atasnya tetap kontras AAA (7.9:1)."""
REPL = [('#f5c400', '#f0c047'), ('#F5C400', '#f0c047'), ('rgba(245,196,0,', 'rgba(240,192,71,'), ('#e3b500', '#d6a12b'), ('#d9ad00', '#d6a12b'),
        ('#b88f00', '#a77612'), ('#d6ab00', '#ddb049')]


def patch(s):
    n = 0
    for a, b in REPL:
        n += s.count(a)
        s = s.replace(a, b)
    return s, n


def layout(s):
    """Margin grafik 2D Plotly dirapatkan (jarak sumbu ke tepi)."""
    a = "margin:{l:70,r:20,t:10,b:55}"
    assert s.count(a) == 1, s.count(a)
    return s.replace(a, "margin:{l:68,r:10,t:6,b:46}")
