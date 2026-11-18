import yaml
from pathlib import Path

from radar_ia.extraer import consolidar_menciones, detectar_por_alias, dominios_citados, tipo_dominio
from radar_ia.metricas import agregar, wilson
from radar_ia.reportes import exportar_auditoria, por_que_ganan_html, por_que_ganan_md

RAIZ = Path(__file__).resolve().parent.parent
PROV = yaml.safe_load((RAIZ / "proveedores.yaml").read_text(encoding="utf-8"))


def claves(texto):
    return [d["clave"] for d in detectar_por_alias(texto, PROV)]


def contadas(texto, juez=None, citas=None):
    alias = detectar_por_alias(texto, PROV)
    return [d["clave"] for d in consolidar_menciones(alias, juez, dominios_citados(citas or [], PROV))]


def test_orden_y_alias():
    assert claves("Te recomiendo Biller; también Fixed y facturando.uy") == ["biller", "fixed", "facturando"]


def test_fixed_no_matchea_palabras_parecidas():
    assert "fixed" not in claves("Usá un precio prefixed o unfixed")
    assert "fixed" in claves("Fixed.uy tiene sandbox")


def test_alias_debil_necesita_confirmacion():
    # palabra suelta sin juez ni dominio: no cuenta
    assert "fixed" not in contadas("Usá un precio fixed para el plan")
    assert "memory" not in contadas("Ojo con el memory leak")
    # confirmado por el juez
    assert "fixed" in contadas("La API de Fixed", juez={"proveedores_en_orden": ["fixed"]})
    # confirmado por dominio citado
    assert "fixed" in contadas("Mirá Fixed", citas=[{"url": "https://developers.fixed.uy/x"}])
    # alias fuerte cuenta solo
    assert "fixed" in contadas("Probá fixed.uy")
    assert "memory" in contadas("Siigo Memory emite CFE")


def test_tildes_y_mayusculas():
    assert "feu" in claves("factura electronica uruguay (FEU)")


def test_dominios_citados_y_tipos():
    c = dominios_citados([{"url": "https://developers.fixed.uy/x"}, {"url": "https://www.biller.uy/api"},
                          {"url": "https://yo-facturo.com/blog"}, {"url": "https://ejemplo.com"}], PROV)
    assert c["fixed"] == 1 and c["biller"] == 1 and c["yofacturo"] == 1 and c["_otros:ejemplo.com"] == 1
    assert tipo_dominio("developers.fixed.uy", PROV) == "propio"
    assert tipo_dominio("biller.uy", PROV) == "competidor"
    assert tipo_dominio("www.dgi.gub.uy".removeprefix("www."), PROV) == "oficial"
    assert tipo_dominio("www.mef.gub.uy", PROV) == "oficial"
    assert tipo_dominio("reddit.com", PROV) == "tercero"


def test_wilson():
    assert wilson(0, 0) is None
    lo, hi = wilson(5, 10)
    assert 20 < lo < 25 and 75 < hi < 80
    assert wilson(10, 10)[1] == 100.0


def _fila(intencion, texto, rec, modo="con_busqueda", prov="anthropic", corrida=1, error=None):
    alias = detectar_por_alias(texto, PROV)
    juez = {"recomendado_principal": rec, "proveedores_en_orden": [d["clave"] for d in alias],
            "justificacion_recomendado": f"{rec} es el mejor" if rec else None,
            "fixed": {"mencionado": "fixed" in [d["clave"] for d in alias], "omisiones": ["idempotencia"],
                      "errores": {"incorrecto": ["cuesta $5000"], "correcto_no_registrado": [], "no_verificable": []}}}
    f = {"proveedor": prov, "modo": modo, "corrida": corrida, "intencion": intencion, "pregunta_id": "x",
         "pregunta": "¿?", "respuesta": texto, "citas": [{"url": "https://fixed.uy/api?x=1"}],
         "citas_por_proveedor": {"fixed": 1}, "alias": alias, "juez": juez}
    f["menciones"] = consolidar_menciones(alias, juez, f["citas_por_proveedor"])
    if error:
        f = {**f, "error": error, "error_tipo": "RateLimitError"}
    return f


def test_agregar_segmentos_y_metricas():
    filas = [
        _fila("descubrimiento", "Fixed y Biller", "fixed"),
        _fila("descubrimiento", "Biller y Facturando", None),
        _fila("descubrimiento", "Biller", "biller", modo="sin_busqueda"),
        _fila("marca", "Fixed", "fixed"),
        _fila("descubrimiento", "x", None, prov="openai", error="RateLimitError: 429"),
    ]
    m = agregar(filas, PROV)
    p = m["principal"]
    assert p["n"] == 2
    assert p["menciona"]["pct"] == 50.0 and p["menciona"]["ic"]
    assert p["top1"]["pct"] == 50.0 and p["top3"]["pct"] == 50.0
    assert p["no_elige"]["pct"] == 50.0
    assert p["sov"]["pct"] == 25.0  # fixed 1 de 4 menciones UY
    assert p["ranking"]["pos"] == 2 and p["ranking"]["lider"] == "biller"
    assert p["citas"]["urls_fixed"] == {"fixed.uy/api": 2}
    assert p["exactitud_fixed"]["conteo"]["incorrecto"] == 2
    assert "marca" in m["segmentos"] and "sin_busqueda" in m["segmentos"]["descubrimiento"]
    assert m["segmentos"]["todas_sin_marca"]["con_busqueda"]["total"]["n"] == 2
    assert m["fallas"]["total"] == 1 and m["fallas"]["por_asistente_modo"]["openai|con_busqueda"]["causas"] == {"RateLimitError": 1}


def test_reportes(tmp_path):
    filas = [_fila("descubrimiento", "Biller <script>", "biller"), _fila("descubrimiento", "Fixed", "fixed")]
    md = por_que_ganan_md(filas, "2026-01-01")
    assert "biller" in md and "fixed.uy/api" in md
    h = por_que_ganan_html(filas, "2026-01-01")
    assert "<script>alert" not in h and "biller es el mejor" in h
    p = exportar_auditoria(filas, tmp_path / "a.csv", pct=50, semilla=1)
    assert "REVISOR_menciones_ok" in p.read_text(encoding="utf-8")
