import yaml
from pathlib import Path

from radar_ia.extraer import detectar_por_alias, dominios_citados
from radar_ia.metricas import agregar

PROV = yaml.safe_load((Path(__file__).resolve().parent.parent / "proveedores.yaml").read_text(encoding="utf-8"))


def claves(texto):
    return [d["clave"] for d in detectar_por_alias(texto, PROV)]


def test_orden_y_alias():
    assert claves("Te recomiendo Biller; también Fixed y facturando.uy") == ["biller", "fixed", "facturando"]


def test_fixed_no_matchea_palabras_parecidas():
    # "fixed" como palabra en inglés o dentro de otra palabra no debería confundirse... salvo que sea palabra suelta.
    assert "fixed" not in claves("Usá un precio prefixed o unfixed")
    assert "fixed" in claves("Fixed.uy tiene sandbox")
    assert "fixed" in claves("La API de Fixed")


def test_tildes_y_mayusculas():
    assert "feu" in claves("factura electronica uruguay (FEU)")


def test_dominios_citados():
    c = dominios_citados([{"url": "https://developers.fixed.uy/x"}, {"url": "https://www.biller.uy/api"},
                          {"url": "https://yo-facturo.com/blog"}, {"url": "https://ejemplo.com"}], PROV)
    assert c["fixed"] == 1 and c["biller"] == 1 and c["yofacturo"] == 1 and c["_otros:ejemplo.com"] == 1


def test_agregar_excluye_marca_y_calcula_share():
    base = {"citas": [], "citas_por_proveedor": {}, "proveedor": "anthropic", "modo": "con_busqueda"}
    filas = [
        {**base, "intencion": "categoria", "alias": detectar_por_alias("Fixed y Biller", PROV),
         "juez": {"recomendado_principal": "fixed", "fixed": {"errores": []}}},
        {**base, "intencion": "categoria", "alias": detectar_por_alias("Biller", PROV),
         "juez": {"recomendado_principal": "biller", "fixed": {"errores": []}}},
        {**base, "intencion": "marca", "alias": detectar_por_alias("Fixed", PROV), "juez": None},
    ]
    g = agregar(filas, PROV)["general_sin_marca"]
    assert g["n"] == 2
    assert g["pct_menciona_fixed"] == 50.0
    assert g["pct_fixed_recomendado_principal"] == 50.0
    assert g["share_of_voice_fixed_uy"] == round(100 / 3, 1)
