"""The Agentic Data Scientist (Augmented Learning Labs): paquete del curso para Colab.

El mundo visual del curso es la Taquería de Datos.

Qué hace:
- Aplica el estilo visual del curso a tarjetas y gráficas.
- Identifica al alumno con sus secretos de Colab (TDD_ID y TDD_CLAVE) contra Supabase Auth.
- Registra su avance en Supabase sin duplicados y con reintentos; si algo falla, el cuaderno sigue funcionando
  y los eventos esperan en una cola.
- En modo invitado registra, sin identidad, qué secciones se abren y por qué no hubo sesión.
- Muestra el modo docente solo a la cuenta docente; la base de datos lo hace cumplir.
- Anima el caso como un videojuego de 8 bits (cine): franjas de nivel, tableros que se llenan, barras que crecen,
  sellos que caen. Todo se ve completo aunque no haya JavaScript y respeta «reducir movimiento».

Qué NO hace:
- No guarda ni imprime la clave del alumno.
- No contiene claves secretas: solo la URL del proyecto y la clave pública, que son seguras
  mientras la seguridad por fila esté activa en la base.
"""

import datetime as _dt
import html as _html
import json as _json
import os as _os
import re as _re
import urllib.request as _urlreq

VERSION = "0.6.0"
CURSO_NOMBRE = "The Agentic Data Scientist"
ESCUELA = "Augmented Learning Labs"
TUTORIAL_URL = "https://learninglabs.pages.dev/colab.html"
_ORDINAL = {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto", 5: "quinto"}

# --------------------------------------------------------------------------- estilo

FONDO, HONDO, SUPERFICIE, BORDE = "#fff4d6", "#f2e2bb", "#fffbee", "#c9b48a"
TINTA, TINTA_SUAVE = "#1b2236", "#4a5570"
COMAL, COMAL_TEXTO, ANIL = "#f4a63b", "#a65300", "#6f7ee8"
NOPAL, NOPAL_TEXTO, SALSA, SALSA_TEXTO, ROSA, SUADERO = "#4fb06d", "#1f6b3a", "#e04b3a", "#b02a1c", "#ff9db0", "#9c5a35"
PIXEL, TEXTO = "DejaVu Sans Mono", "DejaVu Sans"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Atkinson+Hyperlegible:wght@400;700&family=VT323&display=swap');
.tdd { font-family: 'Atkinson Hyperlegible', system-ui, sans-serif; color: %(tinta)s; font-size: 17px; line-height: 1.55; max-width: 820px; }
.tdd-card { background: %(sup)s; border: 4px solid %(tinta)s; box-shadow: 6px 6px 0 %(tinta)s; padding: 16px 20px; margin: 8px 8px 16px 0; }
.tdd-comanda { background: %(fondo)s; border-top: 6px dashed %(tinta)s; box-shadow: 6px 6px 0 %(tinta)s; padding: 16px 20px; margin: 8px 8px 16px 0; }
.tdd-docente { background: #1f3150; color: #fff4d6; border: 4px solid #f4a63b; box-shadow: 6px 6px 0 %(tinta)s; padding: 16px 20px; margin: 8px 8px 16px 0; }
.tdd-docente .tdd-h { color: #f4a63b; }
.tdd-docente td, .tdd-docente th { border-color: #3a4d6e; color: #fff4d6; }
.tdd-llm { display: inline-block; background: #fff4d6; color: %(tinta)s; border: 3px dashed %(tinta)s; padding: 8px 12px; margin: 6px 0; font-size: 15px; }
.tdd-h { font-family: 'Press Start 2P', monospace; font-size: 13px; line-height: 1.6; margin: 0 0 10px; }
.tdd-cifra { font-family: 'VT323', monospace; font-size: 48px; line-height: 1; }
.tdd table { border-collapse: collapse; font-size: 16px; }
.tdd th { text-align: left; border-bottom: 4px solid %(tinta)s; padding: 6px 14px 6px 0; }
.tdd td { border-bottom: 2px solid %(borde)s; padding: 6px 14px 6px 0; vertical-align: top; }
.tdd .num { text-align: right; font-variant-numeric: tabular-nums; }
.tdd .flags { display: flex; gap: 6px; margin-bottom: 14px; }
.tdd .flag { width: 30px; height: 22px; clip-path: polygon(0 0,100%% 0,100%% 65%%,50%% 100%%,0 65%%); }
.tdd .barra { display: flex; height: 14px; border: 3px solid currentColor; width: 220px; }
.tdd .chips { display: flex; gap: 12px; flex-wrap: wrap; margin: 6px 0 12px; }
.tdd .chip { border: 3px solid currentColor; padding: 6px 12px; }
.tdd p { margin: 0 0 8px; }
.tdd ul { margin: 0 0 8px 20px; padding: 0; }
.tdd-card, .tdd-comanda, .tdd-docente { animation: tdd-entra .32s steps(4) both; }
@keyframes tdd-entra { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { .tdd-card, .tdd-comanda, .tdd-docente { animation: none; } }
</style>
""" % {"tinta": TINTA, "sup": SUPERFICIE, "fondo": FONDO, "borde": BORDE}


def mostrar(contenido):
    """Muestra HTML con el estilo del curso."""
    from IPython.display import HTML, display
    display(HTML(_CSS + '<div class="tdd">%s</div>' % contenido))


def tarjeta(titulo, cuerpo, color=TINTA, clase="tdd-card"):
    return '<div class="%s"><p class="tdd-h" style="color:%s">%s</p>%s</div>' % (clase, color, titulo, cuerpo)


def esc(texto):
    return _html.escape(str(texto)) if texto is not None else ""


def banderas():
    colores = [COMAL, ANIL, NOPAL, ROSA, SALSA, TINTA] * 3
    return '<div class="flags">%s</div>' % "".join('<div class="flag" style="background:%s"></div>' % c for c in colores)


def configurar_graficas():
    """Descarga las letras del curso (si hay internet) y ajusta matplotlib."""
    global PIXEL, TEXTO
    try:
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except Exception:
        return
    fuentes = {
        "PressStart2P-Regular.ttf": "ofl/pressstart2p/PressStart2P-Regular.ttf",
        "AtkinsonHyperlegible-Regular.ttf": "ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf",
        "AtkinsonHyperlegible-Bold.ttf": "ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf",
    }
    _os.makedirs("fuentes", exist_ok=True)
    for nombre, ruta in fuentes.items():
        destino = _os.path.join("fuentes", nombre)
        if not _os.path.exists(destino):
            try:
                _urlreq.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/" + ruta, destino)
            except Exception:
                continue
        try:
            font_manager.fontManager.addfont(destino)
        except Exception:
            pass
    familias = {f.name for f in font_manager.fontManager.ttflist}
    PIXEL = "Press Start 2P" if "Press Start 2P" in familias else "DejaVu Sans Mono"
    TEXTO = "Atkinson Hyperlegible" if "Atkinson Hyperlegible" in familias else "DejaVu Sans"
    plt.rcParams.update({
        "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
        "font.family": [TEXTO, "DejaVu Sans"], "font.size": 12, "text.color": TINTA,
        "axes.edgecolor": TINTA, "axes.labelcolor": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 2,
        "xtick.major.width": 2, "ytick.major.width": 2, "figure.dpi": 110,
    })


def encabezado(fig, titulo, subtitulo=None):
    """Título en letra pixel y subtítulo legible, alineados a la izquierda."""
    fig.text(0.02, 0.98, titulo, fontfamily=PIXEL, fontsize=11, color=TINTA, ha="left", va="top")
    if subtitulo:
        fig.text(0.02, 0.905, subtitulo, fontsize=12, color=TINTA_SUAVE, ha="left", va="top")


def _md(texto):
    """Markdown mínimo para notas docentes: listas con '- ', párrafos y **negritas**."""
    salida, lista = [], []

    def cerrar():
        if lista:
            salida.append("<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in lista))
            lista.clear()

    for linea in (texto or "").splitlines():
        linea = linea.rstrip()
        fmt = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(linea))
        if linea.startswith("- "):
            lista.append(fmt[2:])
        elif linea:
            cerrar()
            salida.append("<p>%s</p>" % fmt)
        else:
            cerrar()
    cerrar()
    return "".join(salida)


def _segundos_desde(iso):
    try:
        t = _dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return (_dt.datetime.now(_dt.timezone.utc) - t).total_seconds()
    except Exception:
        return float("inf")


def _hace(iso):
    try:
        t = _dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        seg = (_dt.datetime.now(_dt.timezone.utc) - t).total_seconds()
    except Exception:
        return ""
    if seg < 90:
        return "hace un momento"
    if seg < 3600:
        return "hace %d min" % (seg // 60)
    if seg < 86400:
        return "hace %d h" % (seg // 3600)
    return "hace %d días" % (seg // 86400)


# --------------------------------------------------------------------------- cine: dinamismo 8 bits
#
# Pantallas de arcade dentro del cuaderno: la misma sensación de videojuego de la intro del caso en la página.
# Reglas:
# - Todo se dibuja ya en su estado final (HTML y SVG). Si el navegador no corre JavaScript (vista previa de GitHub,
#   pruebas, lector de pantalla) se ve completo; con JavaScript, el script lo esconde y lo anima.
# - Con «reducir movimiento» del sistema no hay animación.
# - Nada se descarga de terceros salvo las letras del curso (las mismas de mostrar()). No guarda nada ni registra nada.
# - Los textos en letra pixel (títulos, sellos, rótulos de SVG) van sin acentos ni eñe.

PANTALLA, CASILLA, PAPEL, MANILA = TINTA, "#3a4466", "#fffbee", "#e8c77a"

_CINE_CSS = """
<style>
.cine { position: relative; overflow: hidden; background: %(pantalla)s; color: %(fondo)s; border: 4px solid %(tinta)s;
  box-shadow: 6px 6px 0 %(comal)s; padding: 16px 18px 14px; margin: 8px 8px 18px 0; max-width: 780px;
  font-family: 'Atkinson Hyperlegible', system-ui, sans-serif; font-size: 17px; line-height: 1.5; }
.cine-t { font-family: 'Press Start 2P', monospace; font-size: 12px; line-height: 1.7; color: %(comal)s; margin: 0 0 10px; padding-right: 128px; }
.cine-pie { font-size: 15px; color: #cfd6ea; margin: 8px 0 0; }
.cine svg { display: block; width: 100%%; height: auto; shape-rendering: crispEdges; }
.cine svg text { shape-rendering: auto; }
.cine-otra { position: absolute; top: 10px; right: 10px; font-family: 'Press Start 2P', monospace; font-size: 9px;
  background: transparent; color: %(fondo)s; border: 3px solid %(fondo)s; padding: 6px 8px; cursor: pointer; }
.cine-otra:hover { color: %(comal)s; border-color: %(comal)s; }
.cine-otra:focus-visible { outline: 3px solid %(comal)s; outline-offset: 2px; }
.cine.con-sello { padding-bottom: 74px; }
.cine-fila { display: flex; gap: 18px; align-items: center; flex-wrap: wrap; }
.cine-fila > svg { width: 170px; flex: 0 0 auto; }
.cine-texto { flex: 1 1 300px; min-width: 240px; }
.cine-texto p { margin: 0 0 8px; min-height: 1.5em; }
.cine-sello { position: absolute; right: 22px; bottom: 18px; transform: rotate(-9deg); border: 4px solid currentColor;
  padding: 8px 12px; font-family: 'Press Start 2P', monospace; font-size: 13px; line-height: 1.3; background: rgba(27,34,54,.55); }
.cine-claro { background: %(sup)s; color: %(tinta)s; box-shadow: 6px 6px 0 %(tinta)s; border-top: 6px dashed %(tinta)s; }
.cine-claro .cine-t { color: %(salsa_t)s; }
.cine-claro .cine-sello { background: rgba(255,251,238,.7); }
.cine-claro .cine-otra { color: %(tinta)s; border-color: %(tinta)s; }
.cine-num { font-family: 'VT323', monospace; font-size: clamp(40px, 11vw, 64px); line-height: 1; color: %(comal)s; }
.cine-chip { font-family: 'Press Start 2P', monospace; font-size: 10px; border: 3px solid currentColor; padding: 6px 8px; }
.cine-nivel { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; padding: 10px 14px; box-shadow: 5px 5px 0 %(comal)s;
  animation: cine-desliza .45s steps(6) both; }
.cine-nivel .cine-t { margin: 0; padding: 0; color: %(fondo)s; }
.cine-prog { flex: 1 1 140px; min-width: 120px; height: 12px; border: 3px solid %(fondo)s; }
.cine-prog i { display: block; height: 100%%; background: %(nopal)s; animation: cine-llena 1.1s steps(10) .25s both; }
.cine-moneda { display: inline-block; width: 14px; height: 14px; background: %(comal)s; box-shadow: inset -3px -3px 0 %(comal_t)s; margin-right: 4px; }
.cine-js .cine-oculto { opacity: 0; }
.cine-golpe { animation: cine-golpe .32s steps(5) both; }
.cine-aparece { animation: cine-aparece .3s steps(4) both; }
.cine-tiembla { animation: cine-tiembla .42s steps(1) 1; }
.cine-entra { animation: cine-entra .5s steps(6) both; }
.cine-confeti { position: absolute; width: 8px; height: 8px; top: -10px; animation: cine-cae 1.6s steps(12) forwards; pointer-events: none; }
@keyframes cine-golpe { 0%% { opacity: 0; transform: rotate(-9deg) scale(2.6); } 60%% { opacity: 1; } 100%% { opacity: 1; transform: rotate(-9deg) scale(1); } }
@keyframes cine-aparece { from { opacity: 0; transform: scale(.4); } to { opacity: 1; transform: scale(1); } }
@keyframes cine-tiembla { 0%% { transform: translate(4px,-3px); } 20%% { transform: translate(-5px,3px); } 40%% { transform: translate(4px,4px); }
  60%% { transform: translate(-3px,-2px); } 80%% { transform: translate(2px,1px); } 100%% { transform: translate(0,0); } }
@keyframes cine-entra { from { transform: translateX(60px); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes cine-desliza { from { transform: translateX(-40px); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes cine-llena { from { width: var(--desde, 0%%); } }
@keyframes cine-cae { to { transform: translateY(420px) rotate(270deg); opacity: .2; } }
.cine svg .cine-golpe, .cine svg .cine-aparece { transform-box: fill-box; transform-origin: center; }
@media (prefers-reduced-motion: reduce) { .cine, .cine * { animation: none !important; } .cine-otra { display: none; } }
</style>
""" % {"pantalla": PANTALLA, "fondo": FONDO, "tinta": TINTA, "comal": COMAL, "sup": SUPERFICIE, "salsa_t": SALSA_TEXTO,
       "nopal": NOPAL, "comal_t": COMAL_TEXTO}

_CINE_JS = r"""
<script>
(function () {
  if (window.__cine) return;
  var RED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  function qa(r, s) { return Array.prototype.slice.call(r.querySelectorAll(s)); }
  function vivo(r, t) { return r.__tok === t; }
  function luego(r, t, ms, fn) { setTimeout(function () { if (vivo(r, t)) fn(); }, ms); }
  function anim(r, t, ms, fn, fin) {
    var t0 = null;
    function f(n) {
      if (!vivo(r, t)) return;
      if (t0 === null) t0 = n;
      var p = Math.min(1, (n - t0) / ms);
      fn(p);
      if (p < 1) requestAnimationFrame(f); else if (fin) fin();
    }
    requestAnimationFrame(f);
  }
  var sal = function (p) { return 1 - Math.pow(1 - p, 3); };
  var ent = function (p) { return p * p; };
  function fmt(v, d, pre, suf) {
    var s = Number(v).toFixed(d || 0).split('.');
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return (pre || '') + s.join('.') + (suf || '');
  }
  function temblar(r) { r.classList.remove('cine-tiembla'); void r.offsetWidth; r.classList.add('cine-tiembla'); }
  function clase(el, c) { el.classList.remove(c); void el.getBoundingClientRect(); el.classList.add(c); }
  function attr(el, n, d) { var v = el.getAttribute(n); return v === null ? d : v; }

  // Cada paso: prep (deja el estado inicial) y run (anima y avisa al terminar).
  var P = {
    entrar: {
      prep: function (r) { qa(r, '.cine-desliza').forEach(function (e) { e.classList.add('cine-oculto'); }); },
      run: function (r, t, listo) {
        qa(r, '.cine-desliza').forEach(function (e) { e.classList.remove('cine-oculto'); clase(e, 'cine-entra'); });
        luego(r, t, 450, listo);
      }
    },
    tipear: {
      prep: function (r) { qa(r, '[data-texto]').forEach(function (e) { e.textContent = ''; }); },
      run: function (r, t, listo) {
        var ls = qa(r, '[data-texto]'), i = 0;
        (function sig() {
          if (!vivo(r, t)) return;
          if (i >= ls.length) return listo();
          var el = ls[i++], tx = el.getAttribute('data-texto'), k = 0;
          var id = setInterval(function () {
            if (!vivo(r, t)) { clearInterval(id); return; }
            k += 2; el.textContent = tx.slice(0, k);
            if (k >= tx.length) { clearInterval(id); luego(r, t, 320, sig); }
          }, 26);
        })();
      }
    },
    cascada: {
      prep: function (r) { qa(r, '[data-f]').forEach(function (e) { e.style.opacity = 0; }); },
      run: function (r, t, listo) {
        var bs = qa(r, '[data-f]'), f0 = -1;
        anim(r, t, 900, function (p) {
          var f = Math.floor(p * 10.99);
          if (f === f0) return; f0 = f;
          bs.forEach(function (e) { e.style.opacity = (+e.getAttribute('data-f') < f) ? 1 : 0; });
        }, function () { bs.forEach(function (e) { e.style.opacity = 1; }); listo(); });
      }
    },
    marcar: {
      prep: function (r) {
        qa(r, '[data-g]').forEach(function (e) { e.style.opacity = 0; });
        qa(r, '[data-cont]').forEach(function (e) { e.textContent = attr(e, 'data-pre', '') + '0'; });
      },
      run: function (r, t, listo) {
        var cs = qa(r, '[data-cont]'), grupos = {};
        qa(r, '[data-g]').forEach(function (e) { (grupos[e.getAttribute('data-g')] = grupos[e.getAttribute('data-g')] || []).push(e); });
        var ms = +attr(r, 'data-ms', 3200), n0 = {};
        anim(r, t, ms, function (p) {
          var q = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
          Object.keys(grupos).forEach(function (g) {
            var ls = grupos[g], n = Math.round(q * ls.length);
            for (var i = n0[g] || 0; i < n; i++) ls[i].style.opacity = 1;
            n0[g] = Math.max(n0[g] || 0, n);
          });
          cs.forEach(function (c) { c.textContent = fmt(q * +c.getAttribute('data-v'), +attr(c, 'data-dec', 0), attr(c, 'data-pre', ''), ''); });
        }, function () {
          cs.forEach(function (c) { c.textContent = c.getAttribute('data-fin'); });
          temblar(r); listo();
        });
      }
    },
    crecer: {
      prep: function (r) {
        qa(r, '.cine-barra').forEach(function (e) { e.setAttribute('y', e.getAttribute('data-base')); e.setAttribute('height', 0); });
        qa(r, '.cine-val').forEach(function (e) { e.textContent = ''; });
        qa(r, '.cine-tras, .cine-chk').forEach(function (e) { e.style.opacity = 0; });
      },
      run: function (r, t, listo) {
        var bs = qa(r, '.cine-barra'), vs = qa(r, '.cine-val'), n = 0;
        var orden = {};
        bs.forEach(function (b, k) { var i = +b.getAttribute('data-i'); (orden[i] = orden[i] || []).push(k); });
        var pasos = Object.keys(orden).map(Number).sort(function (a, b) { return a - b; });
        if (!pasos.length) return listo();
        var paso = +attr(r, 'data-paso', 170);
        pasos.forEach(function (i, j) {
          luego(r, t, j * paso, function () {
            orden[i].forEach(function (k) {
              var b = bs[k], v = vs[k], base = +b.getAttribute('data-base'), h = +b.getAttribute('data-h');
              anim(r, t, 480, function (p) {
                var hh = h * sal(p);
                b.setAttribute('y', base - hh); b.setAttribute('height', hh);
                if (v) v.textContent = fmt(+v.getAttribute('data-v') * sal(p), +attr(v, 'data-dec', 0), '', attr(v, 'data-suf', ''));
              });
            });
            qa(r, '.cine-tras[data-tras="' + i + '"]').forEach(function (d) { luego(r, t, 480, function () { d.style.opacity = 1; clase(d, 'cine-aparece'); temblar(r); }); });
            if (j === pasos.length - 1) luego(r, t, 560, function () {
              qa(r, '.cine-chk').forEach(function (c, z) { luego(r, t, z * 120, function () { c.style.opacity = 1; clase(c, 'cine-aparece'); }); });
              luego(r, t, 400, listo);
            });
          });
        });
      }
    },
    llover: {
      prep: function (r) { qa(r, '.cine-gota').forEach(function (e) { e.style.opacity = 0; }); qa(r, '.cine-real').forEach(function (e) { e.style.opacity = 0; }); },
      run: function (r, t, listo) {
        var gs = qa(r, '.cine-gota'), N = gs.length, total = 2600;
        var ys = gs.map(function (g) { return +g.getAttribute('y'); });
        var inicio = gs.map(function (g) { return (+g.getAttribute('data-o') / Math.max(1, N)) * (total - 380); });
        anim(r, t, total, function (p) {
          var T = p * total;
          for (var i = 0; i < N; i++) {
            var q = (T - inicio[i]) / 380;
            if (q <= 0) continue;
            q = Math.min(1, q);
            gs[i].style.opacity = 1;
            gs[i].setAttribute('y', -6 + (ys[i] + 6) * ent(q));
          }
        }, function () {
          gs.forEach(function (g, i) { g.setAttribute('y', ys[i]); g.style.opacity = 1; });
          luego(r, t, 300, function () {
            qa(r, '.cine-real').forEach(function (e) { e.style.opacity = 1; clase(e, 'cine-aparece'); });
            temblar(r); listo();
          });
        });
      }
    },
    camino: {
      prep: function (r) { qa(r, '.cine-paso').forEach(function (e) { e.style.opacity = 0; }); qa(r, '.cine-viajero').forEach(function (e) { e.style.opacity = 0; }); },
      run: function (r, t, listo) {
        var ps = qa(r, '.cine-paso');
        ps.forEach(function (e, i) { luego(r, t, i * 420, function () { e.style.opacity = 1; clase(e, 'cine-aparece'); }); });
        luego(r, t, ps.length * 420 + 200, function () {
          var v = r.querySelector('.cine-viajero');
          if (!v) return listo();
          var pts = v.getAttribute('data-pts').split(' ').map(function (s) { var a = s.split(','); return [+a[0], +a[1]]; });
          v.style.opacity = 1;
          var vueltas = 0;
          (function vuelta() {
            if (!vivo(r, t) || vueltas++ >= 4) return;
            anim(r, t, 2400, function (p) {
              var x = p * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(x)), f = x - i;
              v.setAttribute('x', Math.round(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f));
              v.setAttribute('y', Math.round(pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f));
            }, function () { luego(r, t, 500, vuelta); });
          })();
          listo();
        });
      }
    },
    contar: {
      prep: function (r) { qa(r, '.cine-num[data-v]').forEach(function (e) { e.textContent = fmt(0, +attr(e, 'data-dec', 0), attr(e, 'data-pre', ''), attr(e, 'data-suf', '')); }); },
      run: function (r, t, listo) {
        var es = qa(r, '.cine-num[data-v]');
        anim(r, t, 1500, function (p) {
          es.forEach(function (e) { e.textContent = fmt(+e.getAttribute('data-v') * sal(p), +attr(e, 'data-dec', 0), attr(e, 'data-pre', ''), attr(e, 'data-suf', '')); });
        }, listo);
      }
    },
    sellar: {
      prep: function (r) { qa(r, '.cine-sello').forEach(function (e) { e.style.opacity = 0; }); },
      run: function (r, t, listo) {
        qa(r, '.cine-sello').forEach(function (e) { e.style.opacity = ''; clase(e, 'cine-golpe'); });
        luego(r, t, 260, function () { temblar(r); listo(); });
      }
    },
    aparecer: {
      prep: function (r) { qa(r, '.cine-pop').forEach(function (e) { e.style.opacity = 0; }); },
      run: function (r, t, listo) {
        var es = qa(r, '.cine-pop');
        es.forEach(function (e, i) { luego(r, t, i * 140, function () { e.style.opacity = 1; clase(e, 'cine-aparece'); }); });
        luego(r, t, es.length * 140 + 200, listo);
      }
    },
    confeti: {
      prep: function () {},
      run: function (r, t, listo) {
        var cols = (attr(r, 'data-colores', '#f4a63b,#4fb06d,#6f7ee8,#ff9db0')).split(',');
        for (var i = 0; i < 36; i++) {
          var c = document.createElement('i');
          c.className = 'cine-confeti';
          c.style.left = (Math.random() * 96 + 2) + '%';
          c.style.background = cols[i % cols.length];
          c.style.animationDelay = (Math.random() * .6) + 's';
          r.appendChild(c);
        }
        luego(r, t, 2400, function () { qa(r, '.cine-confeti').forEach(function (c) { c.remove(); }); });
        listo();
      }
    }
  };

  function correr(r) {
    if (!r) return;
    var pasos = (r.getAttribute('data-pasos') || '').split(' ').filter(function (p) { return P[p]; });
    if (RED || !pasos.length) return;
    var t = r.__tok = (r.__tok || 0) + 1;
    r.classList.add('cine-js');
    qa(r, '.cine-confeti').forEach(function (c) { c.remove(); });
    pasos.forEach(function (p) { P[p].prep(r); });
    var i = 0;
    (function sig() { if (!vivo(r, t) || i >= pasos.length) return; P[pasos[i++]].run(r, t, sig); })();
  }
  window.__cine = { correr: correr };
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('.cine-otra');
    if (b) correr(b.closest('.cine'));
  });
})();
</script>
"""


def _r(x, y, w, h, c, extra=""):
    return '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>' % (_n(x), _n(y), _n(w), _n(h), c, (" " + extra) if extra else "")


def _n(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def _tx(x, y, texto, tam, color, ancla="middle", pixel=True, extra=""):
    familia = "'Press Start 2P', monospace" if pixel else "'Atkinson Hyperlegible', sans-serif"
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" font-family="%s"%s>%s</text>'
            % (_n(x), _n(y), _n(tam), color, ancla, familia, (" " + extra) if extra else "", esc(texto)))


def _carpeta(codigo):
    """Expediente pixelado (60 x 44) con la etiqueta del caso."""
    return ('<svg viewBox="0 0 60 44" role="img" aria-label="Expediente del caso %s">' % esc(codigo) +
            _r(4, 4, 20, 6, "#c29a4a") + _r(2, 8, 56, 34, MANILA) + _r(2, 8, 56, 2, "#f2dc9e") + _r(2, 40, 56, 2, "#b8974f") +
            _r(9, 17, 42, 11, PAPEL) + _tx(30, 25, "CASO " + codigo, 4.2, TINTA) + "</svg>")


class _Cine:
    """Escenas animadas para el cuaderno. Cada método muestra una pantalla y no devuelve nada."""

    def _mostrar(self, cuerpo, pasos, clase="", titulo=None, extra="", repetir=True):
        import uuid
        from IPython.display import HTML, display
        ident = "cine-" + uuid.uuid4().hex[:10]
        boton = '<button class="cine-otra" type="button" aria-label="Ver la animación otra vez">&#8635; OTRA VEZ</button>' if (repetir and pasos) else ""
        cabeza = '<p class="cine-t">%s</p>' % esc(titulo) if titulo else ""
        if "cine-sello" in cuerpo:
            clase += " con-sello"
        html = ('<div class="cine %s" id="%s" data-pasos="%s"%s>%s%s%s</div>'
                % (clase, ident, " ".join(pasos), (" " + extra) if extra else "", boton, cabeza, cuerpo))
        script = "<script>window.__cine && window.__cine.correr(document.getElementById('%s'));</script>" % ident
        display(HTML(_CSS + _CINE_CSS + '<div class="tdd">' + html + "</div>" + _CINE_JS + script))

    # -- piezas de narración ---------------------------------------------------
    def nivel(self, titulo, n=None, total=None):
        """Franja de inicio de sección: NIVEL n/total, título y barra de avance que se llena."""
        chip = '<span class="cine-chip">NIVEL %d/%d</span>' % (n, total) if n and total else '<span class="cine-chip">NIVEL</span>'
        barra = ""
        if n and total:
            barra = '<div class="cine-prog" aria-hidden="true"><i style="width:%d%%;--desde:%d%%"></i></div>' % (
                round(100 * n / total), round(100 * (n - 1) / total))
        self._mostrar(chip + '<p class="cine-t">%s</p>' % esc(titulo) + barra, [], "cine-nivel", repetir=False)

    def portada(self, codigo, titulo, lineas, sello="EN INVESTIGACION"):
        """Abre el expediente del caso: el que la intro de la página dejó «sin resolver»."""
        texto = "".join('<p data-texto="%s">%s</p>' % (esc(l), esc(l)) for l in lineas)
        cuerpo = ('<div class="cine-fila"><div class="cine-desliza" style="width:170px">%s</div><div class="cine-texto">%s</div></div>'
                  '<div class="cine-sello" style="color:%s">%s</div>' % (_carpeta(codigo), texto, COMAL, esc(sello)))
        self._mostrar(cuerpo, ["entrar", "tipear", "sellar"], titulo=titulo)

    def expediente(self, titulo, filas, sello="CONFIDENCIAL"):
        """Ficha que se escribe sola, renglón por renglón, y termina con un sello."""
        texto = "".join('<p><b>%s</b> <span data-texto="%s">%s</span></p>' % (esc(k), esc(v), esc(v)) for k, v in filas)
        cuerpo = ('<div class="cine-desliza" style="background:%s;color:%s;border:4px solid %s;padding:14px 16px 6px">%s</div>'
                  '<div class="cine-sello" style="color:%s">%s</div>' % (PAPEL, TINTA, MANILA, texto, SALSA, esc(sello)))
        self._mostrar(cuerpo, ["entrar", "tipear", "sellar"], titulo=titulo)

    def sospechoso(self, nombre, idea, prueba, veredicto="DESCARTADO"):
        """Interrogatorio: la idea y la prueba se escriben solas y cae el sello del veredicto."""
        cuerpo = ('<p><b>La idea:</b> <span data-texto="%s">%s</span></p><p><b>La prueba:</b> '
                  '<span data-texto="%s">%s</span></p><div class="cine-sello" style="color:%s">%s</div>'
                  % (esc(idea), esc(idea), esc(prueba), esc(prueba), SALSA, esc(veredicto)))
        self._mostrar(cuerpo, ["tipear", "sellar"], "cine-claro", titulo="SOSPECHOSO: " + nombre)

    def sello(self, texto, detalle="", color=NOPAL):
        """Sello grande que cae con sacudida (veredicto, logro)."""
        cuerpo = ('<p style="margin:0;padding-right:128px;min-height:1.5em">%s</p><div class="cine-sello" style="color:%s;left:22px;right:auto">%s</div>'
                  % (esc(detalle), color, esc(texto)))
        self._mostrar(cuerpo, ["sellar"])

    def cierre(self, codigo, titulo, lineas, sello="RESUELTO"):
        """Cierre del caso: el expediente se sella como resuelto, con confeti."""
        texto = "".join('<p data-texto="%s">%s</p>' % (esc(l), esc(l)) for l in lineas)
        cuerpo = ('<div class="cine-fila"><div class="cine-desliza" style="width:170px">%s</div><div class="cine-texto">%s</div></div>'
                  '<div class="cine-sello" style="color:%s">%s</div>' % (_carpeta(codigo), texto, NOPAL, esc(sello)))
        self._mostrar(cuerpo, ["entrar", "tipear", "sellar", "confeti"], titulo=titulo)

    def contador(self, valor, texto, decimales=0, prefijo="", sufijo="", color=COMAL, titulo=None):
        """Número grande que sube desde cero."""
        cuerpo = ('<div class="cine-num" style="color:%s" data-v="%s" data-dec="%d" data-pre="%s" data-suf="%s">%s</div><p class="cine-pie">%s</p>'
                  % (color, valor, decimales, esc(prefijo), esc(sufijo),
                     esc(prefijo + ("{:,.%df}" % decimales).format(valor) + sufijo), esc(texto)))
        self._mostrar(cuerpo, ["contar"], titulo=titulo)

    # -- piezas con datos ------------------------------------------------------
    def tablero(self, titulo, grupos, unidad="", pie="", ms=3200):
        """Rejillas de 100 cuadros, una por grupo: cada cuadro es una persona; los marcados se encienden al azar.

        grupos: lista de dict(etq, valor 0..1, texto final del contador, marca, base, con_marca, prefijo, decimales).
        El contador termina en `texto`, que debe ser la cifra honesta (p. ej. «MENOS DE 3»), nunca un redondeo engañoso.
        """
        import random
        ancho = 80 * len(grupos)
        s = ['<svg viewBox="0 0 %d 80" role="img" aria-label="%s">' % (ancho, esc(
            "; ".join("%s: %s" % (g["etq"], g.get("texto", "")) for g in grupos)))]
        for gi, g in enumerate(grupos):
            x0, y0 = 15 + gi * 80, 4
            base, marca = g.get("base", CASILLA), g.get("marca", COMAL)
            for k in range(100):
                s.append(_r(x0 + (k % 10) * 5, y0 + (9 - k // 10) * 5, 4, 4, base, 'data-f="%d"' % (k // 10)))
            exacto = max(0.0, min(1.0, float(g["valor"]))) * 100
            llenos, parcial = int(exacto), exacto - int(exacto)
            orden = list(range(100))
            random.Random(g.get("semilla", 7 + gi)).shuffle(orden)
            for q in range(llenos + (1 if parcial > 0.05 and llenos < 100 else 0)):
                k = orden[q]
                x, y = x0 + (k % 10) * 5, y0 + (9 - k // 10) * 5
                w = 4 if q < llenos else round(4 * parcial, 2)
                hueco = _r(x + 1, y + 1, 2, 2, PANTALLA) if (q < llenos and g.get("con_marca")) else ""
                s.append('<g data-g="%d">%s%s</g>' % (gi, _r(x, y, w, 4, marca), hueco))
            s.append(_tx(x0 + 25, 63, g["etq"], 4.2, "#cfd6ea"))
            fin = g.get("texto") or ("%s %s" % (round(exacto, g.get("decimales", 0)), unidad)).strip()
            s.append(_tx(x0 + 25, 74, fin, 5, FONDO, extra='data-cont="1" data-v="%s" data-dec="%d" data-pre="%s" data-fin="%s"' % (
                round(exacto, 3), g.get("decimales", 0), esc(g.get("prefijo", "")), esc(fin))))
        s.append("</svg>")
        self._mostrar("".join(s) + ('<p class="cine-pie">%s</p>' % esc(pie) if pie else ""), ["cascada", "marcar"],
                      titulo=titulo, extra='data-ms="%d"' % ms)

    def barras(self, titulo, categorias, series, colores=None, sufijo="%", decimales=0, divisor=None, ganador=False,
               ymax=None, pie="", paso=170):
        """Barras que crecen una tras otra, con su valor contando hacia arriba.

        series: lista de (nombre, valores, color). colores: color por categoría (solo con una serie).
        divisor: (después de la categoría i, texto): línea punteada que cae cuando la animación pasa por ahí.
        ganador: marca con ✓ la barra más alta de cada categoría.
        """
        nc, ns = len(categorias), len(series)
        alto_max = ymax or max(max(v) for _, v, _ in series) * 1.15 or 1
        x0, x1, base, techo = 8, 192, 70, 12
        ancho_g = (x1 - x0) / nc
        ancho_b = ancho_g * (0.72 if ns == 1 else 0.84) / ns
        s = ['<svg viewBox="0 0 200 %d" role="img" aria-label="%s">' % (90 if ns == 1 else 96, esc(titulo + ". " + "; ".join(
            "%s: %s" % (c, ", ".join("%s %s" % (n, ("{:.%df}" % decimales).format(v[i]) + sufijo) for n, v, _ in series))
            for i, c in enumerate(categorias))))]
        s.append(_r(x0, base, x1 - x0, 1, "#cfd6ea"))
        for i, cat in enumerate(categorias):
            cx = x0 + ancho_g * (i + 0.5)
            mejor = None
            if ganador and ns > 1:
                orden = sorted(range(ns), key=lambda j: -series[j][1][i])
                mejor = orden[0] if series[orden[0]][1][i] > series[orden[1]][1][i] else None  # empate: sin marca
            for j, (nombre, valores, color) in enumerate(series):
                v = valores[i]
                h = max(0.0, (techo - base) * -1 * v / alto_max)
                x = cx - ancho_b * ns / 2 + j * ancho_b
                c = colores[i] if (colores and ns == 1) else color
                s.append(_r(round(x + 0.4, 2), round(base - h, 2), round(ancho_b - 0.8, 2), round(h, 2), c,
                            'class="cine-barra" data-i="%d" data-base="%s" data-h="%s"' % (i, base, round(h, 2))))
                etiqueta = ("{:.%df}" % decimales).format(v) + sufijo
                s.append(_tx(x + ancho_b / 2, base - h - 2, etiqueta, 3.6 if ns == 1 and nc > 8 else (3.1 if ns * nc >= 10 else 4), FONDO,
                             extra='class="cine-val" data-v="%s" data-dec="%d" data-suf="%s"' % (v, decimales, esc(sufijo))))
                if mejor == j:
                    s.append(_tx(x + ancho_b / 2, base - h - 8, "OK", 3.4, NOPAL, extra='class="cine-chk"'))
            s.append(_tx(cx, base + 7, cat, 5 if len(str(cat)) <= 6 else 4.2, "#cfd6ea", pixel=False))
        if divisor:
            i, texto = divisor
            dx = x0 + ancho_g * (i + 1)
            s.append('<g class="cine-tras" data-tras="%d">%s%s</g>' % (
                i, "".join(_r(dx - 0.5, y, 1, 2, COMAL) for y in range(techo - 4, base, 4)), _tx(dx + 2, techo - 2, texto, 3.6, COMAL, "start")))
        if ns > 1:
            lx = x0
            for nombre, _, color in series:
                s.append(_r(lx, 86, 5, 5, color) + _tx(lx + 7, 90.5, nombre, 5, FONDO, "start", pixel=False))
                lx += 9 + len(nombre) * 3.2
        s.append("</svg>")
        self._mostrar("".join(s) + ('<p class="cine-pie">%s</p>' % esc(pie) if pie else ""), ["crecer"], titulo=titulo,
                      extra='data-paso="%d"' % paso)

    def lluvia(self, valores, real, titulo, rango, bins=30, unidad="", pie="", texto_real=None):
        """Cada resultado simulado cae como un cuadrito en su columna; al final cae el valor real."""
        import random
        lo, hi = rango
        cuenta = [0] * bins
        for v in valores:
            if lo <= v < hi:
                cuenta[min(bins - 1, int((v - lo) / (hi - lo) * bins))] += 1
        x0, x1, base = 8, 192, 70
        ancho = (x1 - x0) / bins
        por_cuadro = max(1, -(-max(cuenta) // 26))
        gotas = []
        for b, n in enumerate(cuenta):
            for k in range(-(-n // por_cuadro)):
                gotas.append((x0 + b * ancho + 0.3, base - 2.2 * (k + 1)))
        orden = list(range(len(gotas)))
        random.Random(1847).shuffle(orden)
        s = ['<svg viewBox="0 0 200 86" role="img" aria-label="%s">' % esc(
            "%s. %d resultados simulados entre %s y %s; el valor real es %s." % (titulo, len(valores), lo, hi, real))]
        s.append(_r(x0, base, x1 - x0, 1, "#cfd6ea"))
        for k in range(int(lo), int(hi) + 1):
            x = x0 + (k - lo) / (hi - lo) * (x1 - x0)
            s.append(_r(x, base + 1, 1, 2, "#cfd6ea") + _tx(x, base + 8, str(k), 3.6, "#cfd6ea"))
        for (x, y), o in zip(gotas, orden):
            s.append(_r(round(x, 2), round(y, 2), round(ancho - 0.6, 2), 1.8, NOPAL, 'class="cine-gota" data-o="%d"' % o))
        rx = x0 + (real - lo) / (hi - lo) * (x1 - x0)
        s.append('<g class="cine-real">%s%s</g>' % (_r(round(rx - 0.8, 2), 10, 1.6, base - 10, SALSA),
                                                     _tx(rx - 2, 9, texto_real or "REAL: %s" % real, 4, SALSA, "end")))
        if unidad:
            s.append(_tx(100, 84, unidad, 4.4, "#cfd6ea", pixel=False))
        s.append("</svg>")
        nota = "Cada cuadrito es %s." % ("un mundo" if por_cuadro == 1 else "%d mundos" % por_cuadro)
        self._mostrar("".join(s) + '<p class="cine-pie">%s %s</p>' % (esc(nota), esc(pie)), ["llover"], titulo=titulo)

    def camino(self, titulo, pasos, pie=""):
        """Cajas que aparecen una tras otra unidas por flechas; un punto recorre el camino."""
        n = len(pasos)
        ancho = 200 / n
        s = ['<svg viewBox="0 0 200 64" role="img" aria-label="%s">' % esc(titulo + ": " + " → ".join(t for t, _ in pasos))]
        pts = []
        for i, (texto, color) in enumerate(pasos):
            x = i * ancho + 4
            w = ancho - 14
            claro = color in (COMAL, NOPAL, ANIL, ROSA, FONDO, MANILA)
            lineas = texto.split("\n") if "\n" in texto else ([texto] if len(texto) < 14 else texto.split(" ", 1))
            caja = _r(x, 14, w, 34, color) + _r(x, 14, w, 2, "rgba(255,255,255,.25)")
            for k, l in enumerate(lineas[:2]):
                caja += _tx(x + w / 2, 31 + (k - (len(lineas[:2]) - 1) / 2) * 7, l, 6, TINTA if claro else FONDO, pixel=False,
                            extra='font-weight="700"')
            flecha = ""
            if i < n - 1:
                ax = x + w + 2
                flecha = (_r(ax, 30, 5, 2, FONDO) + _r(ax + 5, 27, 1, 8, FONDO) + _r(ax + 6, 28, 1, 6, FONDO)
                          + _r(ax + 7, 29, 1, 4, FONDO) + _r(ax + 8, 30, 1, 2, FONDO))
            s.append('<g class="cine-paso">%s%s</g>' % (caja, flecha))
            pts.append("%d,%d" % (round(x + w / 2), 53))
        s.append("".join(_r(x, 54.5, 1, 1, "#5a6385") for x in range(round(4 + (ancho - 14) / 2), round(200 - ancho + 4 + (ancho - 14) / 2), 3)))
        s.append(_r(round(4 + (ancho - 14) / 2), 53, 4, 4, SALSA, 'class="cine-viajero" data-pts="%s"' % " ".join(pts)))
        s.append("</svg>")
        self._mostrar("".join(s) + ('<p class="cine-pie">%s</p>' % esc(pie) if pie else ""), ["camino"], titulo=titulo)

    def bits(self, n, texto="bits ganados"):
        """Monedas y contador de bits (se usa al superar un reto)."""
        monedas = "".join('<span class="cine-moneda cine-pop"></span>' for _ in range(min(10, max(1, int(n) // 10 or 1))))
        cuerpo = ('<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap"><div class="cine-num" data-v="%d" data-pre="+">+%d</div>'
                  '<div><p style="margin:0 0 6px">%s</p>%s</div></div>' % (int(n), int(n), esc(texto), monedas))
        self._mostrar(cuerpo, ["aparecer", "contar", "confeti"], extra='data-colores="%s,%s"' % (COMAL, "#ffd98a"), repetir=False)


cine = _Cine()


# --------------------------------------------------------------------------- conexión

class ErrorBackend(Exception):
    """Error al hablar con la base. temporal=True si vale la pena reintentar más tarde."""

    def __init__(self, mensaje, codigo=None, temporal=False, causa=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.temporal = temporal
        self.causa = causa


COLA_ARCHIVO = ".tdd_pendientes.json"
_TEMPORALES = (408, 425, 429, 500, 502, 503, 504)


def _ahora_iso():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def _leer_credenciales():
    """Lee TDD_ID y TDD_CLAVE de los secretos de Colab; fuera de Colab, de variables de entorno.

    Devuelve (id, clave, mensaje, código). El código explica por qué no hay credenciales
    y se guarda (sin nada más) en el registro anónimo del modo invitado.
    """
    try:
        from google.colab import userdata  # noqa: F401
    except ImportError:
        ident, clave = _os.environ.get("TDD_ID"), _os.environ.get("TDD_CLAVE")
        if ident and clave:
            return _limpiar_id(ident), clave.strip(), None, None
        return None, None, "No estás en Colab y no hay variables TDD_ID y TDD_CLAVE.", "fuera_de_colab"
    try:
        ident = userdata.get("TDD_ID")
        clave = userdata.get("TDD_CLAVE")
    except userdata.SecretNotFoundError:
        return None, None, "No encontré tus secretos TDD_ID y TDD_CLAVE.", "sin_secretos"
    except userdata.NotebookAccessError:
        return None, None, "Tus secretos existen, pero este cuaderno no tiene permiso para leerlos.", "sin_permiso"
    except Exception:
        return None, None, "No pude leer tus secretos de Colab.", "otro"
    if not (ident or "").strip() or not (clave or "").strip():
        return None, None, "Uno de tus secretos está vacío.", "secreto_vacio"
    return _limpiar_id(ident), clave.strip(), None, None


def _limpiar_id(ident):
    """Quita espacios, saltos de línea y comillas que a veces se pegan al copiar el ID."""
    return ident.strip().strip("\"'“”‘’ ").strip()


class Sesion:
    """Conexión de un cuaderno con el registro de progreso del curso.

    Garantías del registro:
    - Cada evento lleva un id_cliente único: reintentar un envío nunca lo duplica.
    - Si no hay conexión, los eventos esperan en una cola que también se guarda en disco
      (sobrevive a reiniciar el entorno de ejecución mientras la máquina de Colab siga viva).
    - Los errores de red y de servidor se reintentan con espera creciente; tras una falla,
      el cuaderno deja de insistir 30 segundos para no hacer esperar al alumno.
    - En modo invitado se registra, sin identidad, qué secciones se abren y por qué no hubo sesión.
    """

    def __init__(self, caso, curso, version_cuaderno):
        import uuid
        self.caso = caso
        self.version = version_cuaderno
        self.url = (curso.get("url") or "").rstrip("/")
        self.clave_publica = curso.get("clave_publica") or ""
        self.dominio = curso.get("dominio_alumnos") or "alumnos.taqueriadedatos.mx"
        self.aviso_url = (curso.get("aviso_url") or "").strip()
        self.registrar_invitados = curso.get("registrar_invitados", True)
        self.cola_archivo = curso.get("cola_archivo") or COLA_ARCHIVO
        self.sesion_id = str(uuid.uuid4())
        self.modo = "invitado"
        self.motivo = None
        self.motivo_codigo = None
        self.usuario_id = None
        self.correo = None
        self.nombre = None
        self.alumno_id = None
        self.es_docente = False
        self.secciones = []
        self.descartados = 0
        self.ultimo_error = None
        self._token = None
        self._credencial = None
        self._cola = []
        self._pausa_hasta = 0.0
        self._material = None
        self._retos = None
        self._vistas = set()
        self.etiquetas = {}
        # [(sección, título en letra pixel)] en orden; lo pone el cuaderno (cuadernos de 0.6.0 en adelante).
        # Con él, cada sección abre con su franja animada «NIVEL n/total».
        self.niveles = None

    # -- HTTP --------------------------------------------------------------
    def _http(self, metodo, ruta, cuerpo=None, prefer=None, reintento=True, intentos=3):
        import time
        import requests
        espera = 0.5
        for intento in range(intentos):
            encabezados = {"apikey": self.clave_publica, "Content-Type": "application/json"}
            if self._token:
                encabezados["Authorization"] = "Bearer " + self._token
            if prefer:
                encabezados["Prefer"] = prefer
            error = None
            try:
                r = requests.request(metodo, self.url + ruta, headers=encabezados,
                                     data=None if cuerpo is None else _json.dumps(cuerpo), timeout=8)
            except Exception as e:
                error = ErrorBackend("Sin conexión con la base de datos (%s)." % type(e).__name__, None, True)
            else:
                if r.status_code == 401 and reintento and self._credencial:
                    reintento = False
                    try:
                        self._entrar(*self._credencial)
                    except ErrorBackend as e:
                        raise ErrorBackend("Se venció tu sesión y no pude renovarla. " + str(e), 401, e.temporal)
                    continue
                if r.status_code < 400:
                    if r.status_code == 204 or not r.content:
                        return None
                    return r.json()
                causa = None
                try:
                    detalle = r.json()
                    msg = detalle.get("message") or detalle.get("msg") or detalle.get("error_description") or str(detalle)
                    causa = detalle.get("error_code") or detalle.get("code")
                except Exception:
                    msg = r.text[:200]
                error = ErrorBackend("%s %s" % (r.status_code, msg), r.status_code, r.status_code in _TEMPORALES, causa)
            if not error.temporal or intento == intentos - 1:
                raise error
            time.sleep(espera)
            espera *= 3
        raise ErrorBackend("Sin respuesta de la base de datos.", None, True)

    def _entrar(self, correo, clave):
        self._token = None
        datos = self._http("POST", "/auth/v1/token?grant_type=password", {"email": correo, "password": clave}, reintento=False)
        self._token = datos["access_token"]
        self.usuario_id = datos["user"]["id"]
        self.correo = datos["user"].get("email", correo)

    def conectar(self):
        if not self.url or not self.clave_publica:
            self.motivo = "El curso todavía no está conectado a la base de datos."
            return self
        ident, clave, motivo, codigo = _leer_credenciales()
        if not ident:
            self.motivo, self.motivo_codigo = motivo, codigo
            return self._como_invitado()
        correo = ident if "@" in ident else "%s@%s" % (ident.lower(), self.dominio)
        try:
            self._entrar(correo, clave)
        except ErrorBackend as e:
            if e.codigo == 400 and e.causa == "email_not_confirmed":
                self.motivo = ("Tu cuenta (%s) existe pero su correo no está confirmado. Pídele a tu profesor que "
                               "vuelva a ejecutar el paso 5 del instalador." % correo)
                self.motivo_codigo = "otro"
            elif e.codigo == 400:
                self.motivo = ("Tu ID o tu clave no coinciden. Intenté entrar como <b>%s</b>. En TDD_ID pon exactamente "
                               "lo que te dio tu profesor (puede ser tu correo de Gmail) y revisa TDD_CLAVE, sin comillas."
                               % esc(correo))
                self.motivo_codigo = "clave_incorrecta"
            else:
                self.motivo = "No pude conectarme al registro del curso. " + str(e)
                self.motivo_codigo = "sin_conexion" if e.temporal else "otro"
            self._token = None
            self.usuario_id = None
            return self._como_invitado()
        self._credencial = (correo, clave)
        try:
            self.es_docente = bool(self._http("POST", "/rest/v1/rpc/es_docente", {}))
            perfil = self._http("GET", "/rest/v1/perfiles?select=alumno_id,nombre&id=eq.%s" % self.usuario_id) or []
            if perfil:
                self.nombre = perfil[0]["nombre"]
                self.alumno_id = perfil[0]["alumno_id"]
            caso = self._http("GET", "/rest/v1/casos?select=secciones&id=eq.%s" % self.caso) or []
            self.secciones = caso[0]["secciones"] if caso else []
        except ErrorBackend as e:
            self.motivo = "Entraste, pero no pude leer tu perfil. " + str(e)
        self.modo = "docente" if self.es_docente else "alumno"
        self._cola = self._leer_cola()
        self.registrar(None, "abrio")
        return self

    def _como_invitado(self):
        self.modo = "invitado"
        if self.registrar_invitados:
            self._cola = self._leer_cola()
            self.registrar(None, "abrio")
        return self

    # -- cola persistente ----------------------------------------------------
    def _llave_cola(self):
        return "invitado" if self.modo == "invitado" else "alumno:%s" % self.usuario_id

    def _leer_todo(self):
        try:
            with open(self.cola_archivo, encoding="utf-8") as f:
                datos = _json.load(f)
            return datos if isinstance(datos, dict) else {}
        except Exception:
            return {}

    def _leer_cola(self):
        anteriores = self._leer_todo().get(self._llave_cola(), [])
        vistos = {x["d"].get("id_cliente") for x in self._cola}
        return [x for x in anteriores if isinstance(x, dict) and x.get("d", {}).get("id_cliente") not in vistos][:2000] + self._cola

    def _guardar_cola(self):
        try:
            todo = self._leer_todo()
            if self._cola:
                todo[self._llave_cola()] = self._cola[-2000:]
            else:
                todo.pop(self._llave_cola(), None)
            temporal = self.cola_archivo + ".tmp"
            with open(temporal, "w", encoding="utf-8") as f:
                _json.dump(todo, f)
            _os.replace(temporal, self.cola_archivo)
        except Exception:
            pass

    @property
    def pendientes(self):
        return len(self._cola)

    # -- registro ----------------------------------------------------------
    def _enviar(self, tabla, filas):
        if tabla == "invitado":
            return self._http("POST", "/rest/v1/rpc/registrar_invitado", {"eventos": filas}, reintento=False)
        return self._http("POST", "/rest/v1/%s?on_conflict=usuario,id_cliente" % tabla, filas,
                          prefer="resolution=ignore-duplicates,return=minimal")

    def _vaciar(self, forzar=False):
        """Envía la cola en lotes de 50. Devuelve True si no queda nada pendiente."""
        import time
        if not self._cola:
            return True
        if not self.url or not self.clave_publica or (self.modo != "invitado" and not self._token):
            return False
        if not forzar and time.time() < self._pausa_hasta:
            return False
        while self._cola:
            tabla = self._cola[0]["t"]
            lote = []
            for x in self._cola:
                if x["t"] != tabla or len(lote) == 50:
                    break
                lote.append(x)
            try:
                self._enviar(tabla, [x["d"] for x in lote])
                enviados = lote
            except ErrorBackend as e:
                self.ultimo_error = str(e)
                if e.temporal or e.codigo == 401:
                    self._pausa_hasta = time.time() + 30
                    self._guardar_cola()
                    return False
                # Error permanente (dato inválido): se prueban uno por uno y se descarta solo el malo.
                enviados = []
                for x in lote:
                    try:
                        self._enviar(tabla, [x["d"]])
                    except ErrorBackend as e2:
                        if e2.temporal or e2.codigo == 401:
                            break
                        self.descartados += 1
                    enviados.append(x)
                if not enviados:
                    self._pausa_hasta = time.time() + 30
                    self._guardar_cola()
                    return False
            ids = {id(x) for x in enviados}
            self._cola = [x for x in self._cola if id(x) not in ids]
        self._pausa_hasta = 0.0
        self._guardar_cola()
        return True

    def _encolar(self, tabla, datos):
        import uuid
        datos = dict(datos, sesion=self.sesion_id)
        datos.setdefault("id_cliente", str(uuid.uuid4()))
        datos.setdefault("creado_cliente", _ahora_iso())
        self._cola.append({"t": tabla, "d": datos})
        if len(self._cola) > 2000:
            del self._cola[: len(self._cola) - 2000]
            self.descartados += 1
        if self._vaciar():
            return True
        self._guardar_cola()
        return False

    def registrar(self, seccion, tipo="seccion", valor=None, id_cliente=None):
        """Guarda un evento. Nunca interrumpe al alumno: si falla, queda en la cola y se reintenta."""
        if seccion and tipo == "seccion":
            self._vistas.add(seccion)
        evento = {"caso": self.caso, "seccion": seccion, "tipo": tipo, "valor": valor or {}, "version": self.version}
        if id_cliente:
            evento["id_cliente"] = id_cliente
        if self.modo == "invitado":
            if not self.registrar_invitados or not self.url or not self.clave_publica:
                return False
            evento["motivo"] = self.motivo_codigo or "otro"
            return self._encolar("invitado", evento)
        return self._encolar("eventos", evento)

    def sincronizar(self):
        """Intenta enviar ya todo lo pendiente (sin esperar la pausa). Devuelve True si no queda nada."""
        return self._vaciar(forzar=True)

    def seccion(self, nombre):
        """Marca una sección como vista, muestra su franja de nivel y, en modo docente, su nota."""
        self.registrar(nombre, "seccion")
        claves = [x[0] for x in (self.niveles or [])]
        if nombre in claves and claves.index(nombre) > 0:
            try:
                cine.nivel(dict(self.niveles)[nombre], claves.index(nombre) + 1, len(claves))
            except Exception:
                pass
        self.nota(nombre)

    def respuesta(self, pregunta, texto, etapa=None):
        """Guarda una respuesta abierta. Devuelve True si ya quedó guardada en la base.

        En modo invitado no se guarda el texto: solo se anota, sin identidad, cuántos caracteres tuvo.
        """
        texto = (texto or "").strip()
        if not texto:
            return False
        if self.modo == "invitado":
            self.registrar(pregunta, "respuesta", {"caracteres": len(texto)})
            return False
        ok = self._encolar("respuestas", {"caso": self.caso, "pregunta": pregunta[:60], "texto": texto[:2000], "etapa": etapa})
        return self.registrar(pregunta, "respuesta", {"caracteres": len(texto)}) and ok

    def hipotesis(self, opcion, razon=""):
        ok = self.registrar("hipotesis", "hipotesis", {"opcion": str(opcion)[:120], "tiene_razon": bool((razon or "").strip())})
        if (razon or "").strip():
            ok = self.respuesta("hipotesis_razon", razon, "inicio") and ok
        return ok

    def control(self, nombre, valor):
        self.registrar(nombre, "control", {"valor": valor})

    def completar(self):
        ok = self.registrar("cierre", "completo")
        return self.sincronizar() and ok

    # -- retos ---------------------------------------------------------------
    def reto(self, reto, respuesta, pista=None):
        """Envía la respuesta de un reto y dice al momento si acertó y cuántos bits vale.

        La respuesta correcta nunca está en el cuaderno: la califica la base (intentar_reto). Si no hay conexión,
        el intento queda en la cola y la base lo califica cuando llegue. En modo invitado no se puede comprobar.
        Devuelve el resultado de la base (dict) o None si no se pudo comprobar.
        """
        import uuid
        dada = str(respuesta if respuesta is not None else "").strip()
        if not dada or dada.startswith("Elige"):
            mostrar(tarjeta("Reto", "<p>Elige o escribe tu respuesta arriba y vuelve a ejecutar la celda con ▶.</p>", TINTA_SUAVE))
            return None
        if self.modo == "invitado":
            self.registrar(reto, "control", {"intento": True})
            mostrar(tarjeta("Reto sin comprobar",
                            "<p>En modo invitado no puedo decirte si acertaste: la respuesta correcta vive en la base del curso y solo "
                            "se consulta con tus secretos. Puedes seguir con el caso sin problema.</p>"
                            "<p>Para que tus retos cuenten, pon tus secretos con el <a href='%s' target='_blank' rel='noopener'>tutorial "
                            "de Colab</a> y vuelve a ejecutar la primera celda.</p>" % esc(TUTORIAL_URL), SALSA_TEXTO))
            return None
        ident = str(uuid.uuid4())
        cuerpo = {"p_caso": self.caso, "p_reto": reto, "p_respuesta": dada[:200], "p_id_cliente": ident,
                  "p_sesion": self.sesion_id, "p_version": self.version, "p_creado_cliente": _ahora_iso()}
        try:
            res = self._http("POST", "/rest/v1/rpc/intentar_reto", cuerpo, intentos=2)
        except ErrorBackend as e:
            if e.temporal or e.codigo == 404:
                # Sin conexión, o la base todavía no tiene intentar_reto: el intento se guarda como evento (mismo id,
                # así que si la base ya lo había recibido no se duplica) y se califica al llegar.
                guardado = self.registrar(reto, "control", {"respuesta": dada[:200]}, id_cliente=ident)
                mostrar(tarjeta("Respuesta guardada sin comprobar",
                                "<p>No pude comprobarla en este momento. %s Vuelve a ejecutar la celda más tarde para ver si acertaste: "
                                "tu primer intento ya quedó contado.</p>" % (
                                    "Ya está en tu registro y se calificará sola." if guardado else
                                    "Quedó en la cola y se enviará sola cuando haya conexión."), COMAL_TEXTO))
                return None
            mensaje = str(e).split(" ", 1)[1] if str(e)[:3].isdigit() else str(e)
            mostrar(tarjeta("Reto", "<p>%s</p>" % esc(mensaje), SALSA_TEXTO))
            return None
        self._mostrar_reto(res or {}, pista)
        if self.modo == "docente":
            self._nota_reto(reto)
        return res

    def _mostrar_reto(self, r, pista):
        if not r.get("existe"):
            return mostrar(tarjeta("Respuesta guardada",
                                   "<p>Tu respuesta quedó en tu registro, pero este reto todavía no tiene respuesta correcta en la base. "
                                   "Cuando tu profesor la cargue, se calificará sola con la regla de siempre.</p>", TINTA_SUAVE))
        n, primer = int(r.get("intento") or 0), r.get("primer_acierto")
        dif = int(r.get("dificultad") or 1)
        nivel = "<span title='Dificultad %d de 3'>%s</span>" % (dif, "★" * dif + "☆" * (3 - dif))
        pista_html = "<p><b>Pista:</b> %s</p>" % esc(pista) if pista else ""
        expl = "<p><b>Por qué:</b> %s</p>" % esc(r["explicacion"]) if r.get("explicacion") else ""
        ganados = 0
        if r.get("acierto") and primer == n:
            ganados = int(r.get("bits") or 0)
            titulo, color = "¡Reto superado!", NOPAL_TEXTO
            cuerpo = ("<p><span class='tdd-cifra'>+%d</span> bits</p><p>%s Acertaste en tu %s intento%s.</p>%s" % (
                r.get("bits", 0), nivel, _ORDINAL.get(n, "%d.º" % n),
                "" if n == 1 else " (al primero valía %d)" % r.get("bits_max", 0), expl))
        elif r.get("acierto"):
            titulo, color = "Correcto", NOPAL_TEXTO
            cuerpo = (("<p>Ya lo habías resuelto en tu %s intento: tus %d bits se quedan.</p>" % (_ORDINAL.get(primer, "%d.º" % primer), r.get("bits", 0)))
                      if primer else "<p>Lo resolviste después del quinto intento: este reto ya no da bits, pero ahora sí lo dominas.</p>") + expl
        elif primer:
            titulo, color = "Esa no es", COMAL_TEXTO
            cuerpo = ("<p>Esta respuesta no es la correcta, pero ya habías resuelto el reto en tu %s intento: tus %d bits se quedan.</p>"
                      % (_ORDINAL.get(primer, "%d.º" % primer), r.get("bits", 0))) + expl
        elif r.get("siguiente_bits"):
            titulo, color = "Todavía no", SALSA_TEXTO
            cuerpo = ("<p>%s Intento %d. Equivocarte no resta: si aciertas en el siguiente, ganas <b>%d bits</b>.</p>%s"
                      % (nivel, n, r["siguiente_bits"], pista_html))
        else:
            titulo, color = "Todavía no", SALSA_TEXTO
            cuerpo = ("<p>Intento %d. Después de cinco intentos el reto ya no da bits, pero puedes seguir intentando para aprenderlo.</p>%s%s"
                      % (n, pista_html, expl))
        mostrar(tarjeta(titulo, cuerpo, color))
        if ganados > 0:
            try:
                cine.bits(ganados)
            except Exception:
                pass

    def _nota_reto(self, reto):
        """Modo docente: respuesta correcta y cómo le va al grupo en ese reto."""
        try:
            if self._retos is None:
                self._retos = {(x["caso"], x["reto"]): x for x in self._http("POST", "/rest/v1/rpc/docente_retos", {}, intentos=2) or []}
            x = self._retos.get((self.caso, reto))
        except ErrorBackend:
            x = None
        if not x:
            return
        tol = float(x.get("tolerancia") or 0)
        acierto = x.get("acierto_primer")
        mostrar(tarjeta("Para ti: reto %s" % esc(reto),
                        "<p><b>Respuesta correcta:</b> %s%s · dificultad %s</p><p>%d alumno(s) lo intentaron; %d lo resolvieron%s.</p>" % (
                            esc(x.get("respuesta")), (" ± %g" % tol) if tol else "", x.get("dificultad"), int(x.get("alumnos") or 0),
                            int(x.get("acertaron") or 0),
                            "" if acierto is None else "; %d%% acertó al primer intento" % round(float(acierto) * 100)),
                        COMAL, "tdd-docente"))

    def avance(self):
        if self.modo == "invitado":
            return {"secciones_vistas": len(self._vistas), "completo": False}
        try:
            filas = self._http("GET", "/rest/v1/vista_avance?caso=eq.%s&usuario=eq.%s" % (self.caso, self.usuario_id), intentos=2) or []
        except ErrorBackend:
            filas = []
        return filas[0] if filas else {"secciones_vistas": len(self._vistas), "completo": False}

    def estado(self):
        """Resumen del registro de esta ejecución, para revisar que todo llegó."""
        guardado = self.sincronizar()
        if self.modo == "invitado":
            titulo = "Registro anónimo" if self.registrar_invitados else "Sin registro"
        else:
            titulo = "Tu registro"
        if guardado:
            cuerpo = "<p style='color:%s'><b>Todo guardado.</b> No hay nada pendiente.</p>" % NOPAL_TEXTO
        else:
            cuerpo = ("<p style='color:%s'><b>%d evento(s) pendientes.</b> Se reintentará solo; si cierras Colab antes, "
                      "vuelve a ejecutar esta celda más tarde.</p>" % (SALSA_TEXTO, len(self._cola)))
        if self.descartados:
            cuerpo += "<p>%d evento(s) no válidos se descartaron.</p>" % self.descartados
        mostrar(tarjeta(titulo, cuerpo))
        return guardado

    # -- tarjetas ----------------------------------------------------------
    def _aviso(self):
        if self.aviso_url.startswith("https://"):
            enlace = '<a href="%s" target="_blank" rel="noopener">aviso de privacidad</a>' % esc(self.aviso_url)
        else:
            enlace = "aviso de privacidad (pídeselo a tu profesor)"
        if self.modo == "invitado" and self.registrar_invitados:
            uso = ("En modo invitado solo se registra, de forma anónima, qué secciones abres; "
                   "no se guarda tu nombre, tu correo ni tus respuestas")
        elif self.modo == "invitado":
            uso = "En modo invitado no se registra nada"
        else:
            uso = "Tu avance y tus respuestas se registran para el seguimiento y la calificación del curso"
        return ("<p style='margin-top:10px;font-size:15px'>%s · %s. %s. Consulta el %s.</p>"
                % (esc(CURSO_NOMBRE), esc(ESCUELA), uso, enlace))

    def tarjeta_inicio(self):
        total = len(self.secciones) or 9
        if self.modo == "invitado":
            cuerpo = ("<p><b>Estás en modo invitado:</b> el cuaderno funciona completo, pero tu avance no cuenta para tu calificación.</p>"
                      "<p>%s</p>" % (self.motivo if self.motivo_codigo == "clave_incorrecta" else esc(self.motivo)) +
                      "<p>Para guardarlo: abre el panel <b>Secretos</b> (la llave en la barra izquierda), crea <code>TDD_ID</code> "
                      "y <code>TDD_CLAVE</code> con los datos que te dio tu profesor, activa <b>Acceso del cuaderno</b> "
                      "y vuelve a ejecutar esta celda. Paso a paso, con imágenes: <a href='%s' target='_blank' rel='noopener'>"
                      "tutorial de Colab</a>.</p>" % esc(TUTORIAL_URL))
            return mostrar(banderas() + tarjeta("Modo invitado", cuerpo + self._aviso(), SALSA_TEXTO))
        av = self.avance()
        vistas = int(av.get("secciones_vistas") or 0)
        lleno = round(100 * min(vistas, total) / total)
        barra = ('<div class="barra"><div style="width:%d%%;background:%s"></div></div>' % (lleno, NOPAL))
        saludo = "Hola, %s." % esc((self.nombre or "").split(" ")[0] or self.alumno_id or "")
        estado = "Caso completado." if av.get("completo") else "Llevas %d de %d secciones de este caso." % (min(vistas, total), total)
        cuerpo = "<p><b>%s</b> %s</p>%s" % (saludo, estado, barra)
        if self._cola:
            cuerpo += ("<p style='color:%s'>Hay %d evento(s) de una sesión anterior esperando conexión; "
                       "se enviarán solos.</p>" % (SALSA_TEXTO, len(self._cola)))
        if self.modo == "docente":
            cuerpo += ("<p style='margin-top:10px'><b>Modo docente activo.</b> Verás notas, rúbricas, marcas de la fase 2 "
                       "y el panel del grupo. Nadie más puede ver este contenido: lo protege la base de datos.</p>")
        mostrar(banderas() + tarjeta("Tu comanda" if self.modo == "alumno" else "Modo docente", cuerpo + self._aviso(),
                                     NOPAL_TEXTO if self.modo == "alumno" else COMAL_TEXTO))

    def confirmar(self, titulo, cuerpo, guardado):
        nota = ""
        if self.modo != "invitado":
            nota = "<p style='color:%s'>%s</p>" % (NOPAL_TEXTO if guardado else SALSA_TEXTO,
                                                   "Guardado en tu registro." if guardado else "Aún no se guardó; se reintentará.")
        mostrar(tarjeta(titulo, cuerpo + nota))

    # -- modo docente ------------------------------------------------------
    def _cargar_material(self):
        if self._material is None:
            try:
                filas = self._http("GET", "/rest/v1/material_docente?select=clave,titulo,contenido,orden&caso=eq.%s&order=orden.asc" % self.caso) or []
            except ErrorBackend:
                filas = []
            self._material = {f["clave"]: f for f in filas}
        return self._material

    def nota(self, clave):
        """Muestra la nota docente de una sección. Para alumnos no muestra nada."""
        if self.modo != "docente":
            return
        m = self._cargar_material().get(clave)
        if m:
            mostrar(tarjeta("Para ti: " + esc(m["titulo"]), _md(m["contenido"]), COMAL, "tdd-docente"))

    def marca_llm(self, descripcion):
        """[LLM · fase 2] Señala dónde irá la retroalimentación con IA. Solo la ve la cuenta docente."""
        if self.modo != "docente":
            return
        mostrar('<div class="tdd-llm"><b>LLM, fase 2.</b> %s</div>' % esc(descripcion))

    def panel(self):
        """Panel del grupo. Solo la cuenta docente recibe datos de otros alumnos."""
        if self.modo != "docente":
            if self.modo == "alumno":
                mostrar("<p style='color:%s'>Esta sección es para tu profesor. Puedes seguir con el cuaderno.</p>" % TINTA_SUAVE)
            return
        try:
            perfiles = self._http("GET", "/rest/v1/perfiles?select=id,alumno_id,nombre,grupo&order=alumno_id.asc") or []
            avance = self._http("GET", "/rest/v1/vista_avance?caso=eq.%s" % self.caso) or []
            hipot = self._http("GET", "/rest/v1/eventos?select=usuario,valor,creado&caso=eq.%s&tipo=eq.hipotesis&order=creado.asc" % self.caso) or []
            resps = self._http("GET", "/rest/v1/respuestas?select=usuario,pregunta,texto,creado&caso=eq.%s&order=creado.desc&limit=300" % self.caso) or []
            try:
                invitados = self._http("GET", "/rest/v1/vista_invitados?caso=eq.%s" % self.caso) or []
            except ErrorBackend:
                invitados = []
        except ErrorBackend as e:
            return mostrar(tarjeta("Panel del grupo", "<p>No pude leer los datos: %s</p>" % esc(e), SALSA_TEXTO, "tdd-docente"))

        alumnos = [p for p in perfiles if p["id"] != self.usuario_id]
        por_id = {p["id"]: p for p in alumnos}
        av = {a["usuario"]: a for a in avance}
        primera_hip = {}
        for h in hipot:
            primera_hip.setdefault(h["usuario"], (h.get("valor") or {}).get("opcion", ""))
        total = len(self.secciones) or 9
        abrieron = sum(1 for p in alumnos if p["id"] in av)
        completaron = sum(1 for p in alumnos if av.get(p["id"], {}).get("completo"))
        activos = sum(1 for p in alumnos if _segundos_desde(av.get(p["id"], {}).get("ultimo_evento")) < 900)

        chips = ('<div class="chips"><div class="chip"><span class="tdd-cifra">%d</span><br>alumnos</div>'
                 '<div class="chip"><span class="tdd-cifra">%d</span><br>abrieron el caso</div>'
                 '<div class="chip"><span class="tdd-cifra">%d</span><br>lo completaron</div>'
                 '<div class="chip"><span class="tdd-cifra">%d</span><br>activos ahora<br><small>últimos 15 min</small></div></div>'
                 ) % (len(alumnos), abrieron, completaron, activos)

        conteo = {}
        for u, op in primera_hip.items():
            if u in por_id:
                conteo[op] = conteo.get(op, 0) + 1
        n_hip = sum(conteo.values())
        barras = ""
        for op, n in sorted(conteo.items(), key=lambda x: -x[1]):
            barras += ('<div style="display:flex;align-items:center;gap:10px;margin:4px 0"><span style="width:240px">%s</span>'
                       '<div style="height:16px;width:%dpx;background:%s"></div><span>%d</span></div>') % (esc(op), max(4, 260 * n // max(1, n_hip)), COMAL, n)
        bloque_hip = "<p><b>Hipótesis iniciales (%d respuestas)</b></p>%s" % (n_hip, barras or "<p>Aún no hay hipótesis.</p>")

        filas = ""
        for p in alumnos:
            a = av.get(p["id"])
            if not a:
                estado, vistas, cuando = "No ha abierto", 0, ""
            else:
                vistas = min(int(a.get("secciones_vistas") or 0), total)
                estado = "Completo ✓" if a.get("completo") else "En curso"
                cuando = _hace(a.get("ultimo_evento"))
                if _segundos_desde(a.get("ultimo_evento")) < 900:
                    estado = "<b style='color:%s'>● activo</b> · %s" % (NOPAL, estado)
            barra = '<div class="barra" style="width:120px"><div style="width:%d%%;background:%s"></div></div>' % (round(100 * vistas / total), NOPAL)
            filas += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s %d/%d</td><td>%s</td><td>%s</td></tr>" % (
                esc(p["alumno_id"]), esc(p["nombre"]), esc(p.get("grupo") or ""), barra, vistas, total, estado + (" · " + cuando if cuando else ""), esc(primera_hip.get(p["id"], "")))
        tabla = ("<table><tr><th>ID</th><th>Nombre</th><th>Grupo</th><th>Avance</th><th>Estado</th><th>Hipótesis</th></tr>%s</table>" % filas
                 if filas else "<p>No hay alumnos registrados todavía.</p>")

        etiquetas = {"hipotesis_razon": "Razón de la hipótesis", "explicacion": "Explicación antes de la pista", "ejemplo": "Ejemplo para su trabajo"}
        etiquetas.update(self.etiquetas or {})
        orden = list(self.etiquetas or {}) + [p for p in ["explicacion", "ejemplo", "hipotesis_razon"] if p not in (self.etiquetas or {})]
        orden += sorted({r["pregunta"] for r in resps} - set(orden))
        bloques = ""
        for pregunta in orden:
            lista = [r for r in resps if r["pregunta"] == pregunta and r["usuario"] in por_id]
            if not lista:
                continue
            items = "".join("<tr><td style='width:140px'>%s</td><td>%s</td><td style='width:110px'>%s</td></tr>" % (
                esc(por_id[r["usuario"]]["nombre"]), esc(r["texto"]), _hace(r["creado"])) for r in lista[:60])
            bloques += "<p style='margin-top:14px'><b>%s (%d)</b></p><table>%s</table>" % (etiquetas.get(pregunta, pregunta), len(lista), items)
        motivos = {"sin_secretos": "no crearon sus secretos", "sin_permiso": "no dieron acceso del cuaderno",
                   "secreto_vacio": "un secreto vacío", "clave_incorrecta": "ID o clave incorrectos",
                   "sin_conexion": "sin conexión", "fuera_de_colab": "fuera de Colab", "otro": "otro motivo"}
        if invitados:
            n_ses = sum(int(i.get("sesiones") or 0) for i in invitados)
            n_fin = sum(int(i.get("completaron") or 0) for i in invitados)
            filas_inv = "".join("<tr><td>%s</td><td class='num'>%s</td><td class='num'>%s</td><td>%s</td></tr>" % (
                esc(motivos.get(i["motivo"], i["motivo"])), i.get("sesiones"), i.get("completaron"), _hace(i.get("ultimo_evento")))
                for i in sorted(invitados, key=lambda x: -int(x.get("sesiones") or 0)))
            bloque_inv = ("<p style='margin-top:14px'><b>Modo invitado: %d ejecución(es) anónimas, %d llegaron al cierre</b></p>"
                          "<p>Si hay muchas por ID o clave incorrectos o por secretos faltantes, conviene repasar la configuración en clase.</p>"
                          "<table><tr><th>Por qué entraron como invitado</th><th>Ejecuciones</th><th>Al cierre</th><th>Última</th></tr>%s</table>"
                          % (n_ses, n_fin, filas_inv))
        else:
            bloque_inv = "<p style='margin-top:14px'><b>Modo invitado:</b> nadie ha abierto este caso sin sesión.</p>"
        marca = ('<div class="tdd-llm" style="margin-top:12px"><b>LLM, fase 2.</b> Aquí se agruparán las respuestas por nivel de la rúbrica '
                 'y por error conceptual, para que veas de un vistazo qué parte del grupo necesita la pregunta de rescate.</div>')
        mostrar(tarjeta("Panel del grupo, caso %s" % esc(self.caso),
                        chips + bloque_hip + "<p style='margin-top:14px'><b>Avance por alumno</b></p>" + tabla +
                        (bloques or "<p style='margin-top:14px'>Aún no hay respuestas abiertas.</p>") + bloque_inv + marca,
                        COMAL, "tdd-docente"))


def iniciar(caso, curso, version_cuaderno="1"):
    """Prepara el estilo, identifica al alumno y muestra su tarjeta de inicio."""
    configurar_graficas()
    sesion = Sesion(caso, curso, version_cuaderno).conectar()
    sesion.tarjeta_inicio()
    return sesion
