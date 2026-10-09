"""
Prueba arquitectónica (requisito 18): la capa de Negocio debe
permanecer independiente de SQL y de HTTP.

Analiza el código fuente de negocio/domain y negocio/services (donde
viven las reglas de negocio) y falla si aparece algún import de
sqlite3, del paquete http o del módulo json como formato de
transporte.
"""

import ast
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS_DE_REGLAS_DE_NEGOCIO = [
    os.path.join(BASE_DIR, "negocio", "domain"),
    os.path.join(BASE_DIR, "negocio", "services"),
]

IMPORTS_PROHIBIDOS = {"sqlite3", "http", "http.server", "json"}


class TestAislamientoDeCapas(unittest.TestCase):
    def test_negocio_no_importa_sql_ni_http(self):
        infracciones = []
        for carpeta in MODULOS_DE_REGLAS_DE_NEGOCIO:
            for nombre_archivo in os.listdir(carpeta):
                if not nombre_archivo.endswith(".py"):
                    continue
                ruta = os.path.join(carpeta, nombre_archivo)
                arbol = ast.parse(open(ruta, encoding="utf-8").read(), filename=ruta)
                for nodo in ast.walk(arbol):
                    nombres_importados = []
                    if isinstance(nodo, ast.Import):
                        nombres_importados = [alias.name for alias in nodo.names]
                    elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                        nombres_importados = [nodo.module]
                    for nombre in nombres_importados:
                        raiz = nombre.split(".")[0]
                        if raiz in IMPORTABLES_TERCEROS_PERMITIDOS:
                            continue
                        if nombre in IMPORTS_PROHIBIDOS or raiz in IMPORTS_PROHIBIDOS:
                            infracciones.append(f"{ruta}: import prohibido '{nombre}'")
        self.assertEqual(infracciones, [], "\n".join(infracciones))

    def test_negocio_no_contiene_sentencias_sql_literales(self):
        palabras_sql = ("SELECT ", "INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE")
        infracciones = []
        for carpeta in MODULOS_DE_REGLAS_DE_NEGOCIO:
            for nombre_archivo in os.listdir(carpeta):
                if not nombre_archivo.endswith(".py"):
                    continue
                ruta = os.path.join(carpeta, nombre_archivo)
                contenido = open(ruta, encoding="utf-8").read().upper()
                for palabra in palabras_sql:
                    if palabra in contenido:
                        infracciones.append(f"{ruta}: contiene SQL literal ('{palabra.strip()}')")
        self.assertEqual(infracciones, [], "\n".join(infracciones))


IMPORTABLES_TERCEROS_PERMITIDOS = {
    "dataclasses", "typing", "enum", "abc", "re",
    "negocio",
}


if __name__ == "__main__":
    unittest.main()
