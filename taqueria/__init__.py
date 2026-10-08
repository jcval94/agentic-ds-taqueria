"""The Agentic Data Scientist (Augmented Learning Labs): paquete del curso para Colab.

El mundo visual del curso es la Taquería de Datos.

Qué hace:
- Aplica el estilo visual del curso a tarjetas y gráficas.
- Identifica al alumno con sus secretos de Colab (TDD_ID y TDD_CLAVE) contra Supabase Auth.
- Registra su avance en Supabase sin duplicados y con reintentos; si algo falla, el cuaderno sigue funcionando
  y los eventos esperan en una cola.
- En modo invitado registra, sin identidad, qué secciones se abren y por qué no hubo sesión.
- Muestra el modo docente solo a la cuenta docente; la base de datos lo hace cumplir.

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

VERSION = "0.4.0"
CURSO_NOMBRE = "The Agentic Data Scientist"
ESCUELA = "Augmented Learning Labs"

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


# --------------------------------------------------------------------------- conexión

class ErrorBackend(Exception):
    """Error al hablar con la base. temporal=True si vale la pena reintentar más tarde."""

    def __init__(self, mensaje, codigo=None, temporal=False):
        super().__init__(mensaje)
        self.codigo = codigo
        self.temporal = temporal


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
            return ident.strip(), clave, None, None
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
    if not ident or not clave:
        return None, None, "Uno de tus secretos está vacío.", "secreto_vacio"
    return ident.strip(), clave, None, None


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
        self._vistas = set()

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
                try:
                    detalle = r.json()
                    msg = detalle.get("message") or detalle.get("msg") or detalle.get("error_description") or str(detalle)
                except Exception:
                    msg = r.text[:200]
                error = ErrorBackend("%s %s" % (r.status_code, msg), r.status_code, r.status_code in _TEMPORALES)
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
            if e.codigo == 400:
                self.motivo = ("Tu ID o tu clave no coinciden. En TDD_ID pon exactamente lo que te dio tu profesor "
                               "(puede ser tu correo de Gmail) y revisa TDD_CLAVE.")
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
        datos = dict(datos, id_cliente=str(uuid.uuid4()), sesion=self.sesion_id, creado_cliente=_ahora_iso())
        self._cola.append({"t": tabla, "d": datos})
        if len(self._cola) > 2000:
            del self._cola[: len(self._cola) - 2000]
            self.descartados += 1
        if self._vaciar():
            return True
        self._guardar_cola()
        return False

    def registrar(self, seccion, tipo="seccion", valor=None):
        """Guarda un evento. Nunca interrumpe al alumno: si falla, queda en la cola y se reintenta."""
        if seccion and tipo == "seccion":
            self._vistas.add(seccion)
        evento = {"caso": self.caso, "seccion": seccion, "tipo": tipo, "valor": valor or {}, "version": self.version}
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
        """Marca una sección como vista y, en modo docente, muestra su nota."""
        self.registrar(nombre, "seccion")
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
                      "<p>%s</p>" % esc(self.motivo) +
                      "<p>Para guardarlo: abre el panel <b>Secretos</b> (la llave en la barra izquierda), crea <code>TDD_ID</code> "
                      "y <code>TDD_CLAVE</code> con los datos que te dio tu profesor, activa <b>Acceso del cuaderno</b> "
                      "y vuelve a ejecutar esta celda.</p>")
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

        chips = ('<div class="chips"><div class="chip"><span class="tdd-cifra">%d</span><br>alumnos</div>'
                 '<div class="chip"><span class="tdd-cifra">%d</span><br>abrieron el caso</div>'
                 '<div class="chip"><span class="tdd-cifra">%d</span><br>lo completaron</div></div>') % (len(alumnos), abrieron, completaron)

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
            barra = '<div class="barra" style="width:120px"><div style="width:%d%%;background:%s"></div></div>' % (round(100 * vistas / total), NOPAL)
            filas += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s %d/%d</td><td>%s</td><td>%s</td></tr>" % (
                esc(p["alumno_id"]), esc(p["nombre"]), esc(p.get("grupo") or ""), barra, vistas, total, estado + (" · " + cuando if cuando else ""), esc(primera_hip.get(p["id"], "")))
        tabla = ("<table><tr><th>ID</th><th>Nombre</th><th>Grupo</th><th>Avance</th><th>Estado</th><th>Hipótesis</th></tr>%s</table>" % filas
                 if filas else "<p>No hay alumnos registrados todavía.</p>")

        etiquetas = {"hipotesis_razon": "Razón de la hipótesis", "explicacion": "Explicación antes de la pista", "ejemplo": "Ejemplo para su trabajo"}
        bloques = ""
        for pregunta in ["explicacion", "ejemplo", "hipotesis_razon"]:
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
