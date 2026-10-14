# Visor de Visita Técnica — Diapirismo de Lodo · Golfo de Urabá

**UNGRD – Subdirección para el Conocimiento del Riesgo (SCR)**

Visor cartográfico interactivo de la visita técnica de reconocimiento a los
**volcanes de lodo (diapirismo de lodo)** del Golfo de Urabá (Antioquia),
reactivados tras el **sismo de Panamá del 9 de octubre de 2026**.

## 🌐 Ver el visor en línea

Una vez habilitado GitHub Pages (ver abajo), el visor queda disponible en:

**https://jorgealpala.github.io/diapirismolodo_golfouraba/VISOR_DIAPIRISMO.html**

## 🗺️ Contenido

El visor integra, para cada volcán:

- **Recorrido (track GPS)** del día de la visita.
- **Puntos GPS de referencia** (waypoints).
- **Fotografías con celular** georreferenciadas.
- **Fotografías con dron** (coordenadas del EXIF).
- **Vistas 360°** (Kuula).
- **Selector de volcanes** para enfocar cada sitio.
- Capas base de **Esri** (satélite, topográfico, calles) y leyenda.

### Herramientas de edición cartográfica

- **Dibujar** polígonos, líneas, rectángulos, círculos y puntos.
- **Medir** automáticamente distancias (líneas) y áreas/perímetros (polígonos).
- **Editar y borrar** cualquier dibujo (barra de herramientas del mapa).
- **Anotaciones de texto** sobre el mapa.
- **Exportar a PNG y PDF** (con los dibujos y un encabezado institucional) e **Imprimir**.

Sitios incluidos:

| Volcán | Municipio | Fecha |
|---|---|---|
| Volcán Puerto López | Turbo (Vda. Puerto López) | 11-oct-2026 |
| El Volcán | Necoclí (Vda. El Volcán) | 12-oct-2026 |
| Volcán Las Changas | Necoclí (Vda. Las Changas) | 13-oct-2026 |

> Datum **WGS84 (EPSG:4326)**.

## 📂 Estructura del repositorio

```
VISOR_DIAPIRISMO.html     Visor (datos incrustados; abrir con doble clic o en Pages)
VISOR/
  ├─ datos.js             Datos geoespaciales (tracks, puntos, fotos)
  └─ thumbs/              Miniaturas optimizadas de las fotografías
LOGO/                     Logo institucional UNGRD
ACTUALIZAR_VISOR.py       Script para regenerar el visor cuando hay datos nuevos
MEMORIA_TECNICA_*.docx    Memoria técnica de la visita
```

> **Nota:** las **fotografías originales y los videos** (≈5 GB) no se incluyen
> en el repositorio por los límites de tamaño de GitHub. El visor funciona con
> las miniaturas; el enlace *"Abrir original"* funciona en la copia local que
> contiene la carpeta `DATOS/`.

## 🔄 Actualizar con datos nuevos

Con Python (geopandas + Pillow) instalado, desde esta carpeta:

```bash
python ACTUALIZAR_VISOR.py
```

Relee los shapefiles, regenera miniaturas y actualiza el visor. Para agregar un
volcán nuevo, edita el diccionario `SITES` al inicio de `ACTUALIZAR_VISOR.py`.

## ⚙️ Habilitar GitHub Pages

1. En el repositorio: **Settings → Pages**.
2. En *Build and deployment* → *Source*: **Deploy from a branch**.
3. Branch: **main** / carpeta **/ (root)** → **Save**.
4. Espera ~1 minuto y abre la URL del visor indicada arriba.

---

*Unidad Nacional para la Gestión del Riesgo de Desastres — Subdirección para el Conocimiento del Riesgo.*
