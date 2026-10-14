# -*- coding: utf-8 -*-
"""
==============================================================================
 ACTUALIZAR_VISOR.py  —  UNGRD-SCR · Diapirismo Golfo de Urabá
==============================================================================
Relee TODOS los shapefiles (tracks, puntos GPS, coordenadas de fotos),
extrae el GPS de las fotos de dron (EXIF), regenera las miniaturas y
ACTUALIZA automáticamente el visor (VISOR_DIAPIRISMO.html) conservando el
logo, los estilos y los colores institucionales.

CÓMO USARLO
-----------
1) Abre una terminal en esta carpeta y ejecuta:
       python ACTUALIZAR_VISOR.py
2) Vuelve a abrir (o recarga) VISOR_DIAPIRISMO.html en el navegador.

CÓMO AGREGAR UN VOLCÁN NUEVO
----------------------------
- Crea su carpeta dentro de DATOS/ con la misma estructura:
      DATOS/<FECHA_NOMBRE>/GPS/      -> shapefiles de PUNTOS y TRACK
      DATOS/<FECHA_NOMBRE>/CELULAR/  -> fotos .jpg + shape COORDENADAS_FOTOS
      DATOS/<FECHA_NOMBRE>/DRON/     -> fotos .JPG (y video .MP4 opcional)
- Agrega una entrada en el diccionario SITES de abajo (clave corta única +
  carpeta + metadatos). Los nombres exactos de los .shp se detectan solos.
- Vuelve a ejecutar este script.

Requisitos: Python con geopandas y Pillow (PIL). (Ya instalados en este equipo.)
==============================================================================
"""

import os, sys, glob, json, re, warnings
warnings.filterwarnings('ignore')

BASE   = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE, 'DATOS')
VISOR  = os.path.join(BASE, 'VISOR')
THUMBS = os.path.join(VISOR, 'thumbs')
HTML   = os.path.join(BASE, 'VISOR_DIAPIRISMO.html')
THUMB_MAX, THUMB_Q = 480, 72

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE VOLCANES  (edita aquí para agregar / cambiar volcanes)
#   clave : identificador corto y único (p.ej. 'PL', 'EV', 'V3' ...)
#   dir   : nombre de la carpeta dentro de DATOS/
#   meta  : datos que se muestran en el visor
#           color  = color del recorrido (track) de ese volcán
#           kuula  = lista de vistas 360 (t = etiqueta, url = enlace Kuula)
# ---------------------------------------------------------------------------
SITES = {
 'PL': dict(dir='20261011_PUERTOLOPEZ',
            meta=dict(nombre='Volcán Puerto López', municipio='Turbo',
                      vereda='Vda. Puerto López', correg='Correg. Nuevo Antioquia',
                      fecha='11-oct-2026', color='#ff7a1a',
                      kuula=[{'t':'360 — Parte 1','url':'https://kuula.co/share/collection/7dPhX?logo=1&info=1&fs=1&vr=0&sd=1&thumbs=1'},
                             {'t':'360 — Parte 2','url':'https://kuula.co/share/collection/7dPhc?logo=1&info=1&fs=1&vr=0&sd=1&thumbs=1'}])),
 'EV': dict(dir='20261012_ELVOLCAN',
            meta=dict(nombre='El Volcán', municipio='Necoclí',
                      vereda='Vda. El Volcán', correg='',
                      fecha='12-oct-2026', color='#19c37d',
                      kuula=[{'t':'360','url':'https://kuula.co/share/collection/7dPdG?logo=1&info=1&fs=1&vr=0&sd=1&thumbs=1'}])),
 'LC': dict(dir='20261013_VOLCANLASCHANGAS',
            meta=dict(nombre='Volcán Las Changas', municipio='Necoclí',
                      vereda='Vda. Las Changas', correg='',
                      fecha='13-oct-2026', color='#0cc0df',
                      kuula=[{'t':'360','url':'https://kuula.co/share/collection/7dY5N?logo=0&info=1&fs=1&vr=0&sd=1&thumbs=1'}])),
}
# ---------------------------------------------------------------------------

try:
    import geopandas as gpd
    from shapely.geometry import mapping
    from PIL import Image, ImageOps
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError as e:
    sys.exit('Falta una librería: %s\nInstala con:  pip install geopandas pillow' % e)


def find_one(folder, *patterns):
    for pat in patterns:
        hits = sorted(glob.glob(os.path.join(folder, pat)))
        if hits:
            return hits[0]
    return None


def make_thumb(src_abs, rel_out):
    out_abs = os.path.join(THUMBS, rel_out)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    if not os.path.exists(out_abs):
        try:
            im = Image.open(src_abs)
            im = ImageOps.exif_transpose(im)
            im.thumbnail((THUMB_MAX, THUMB_MAX))
            if im.mode in ('RGBA', 'P'):
                im = im.convert('RGB')
            im.save(out_abs, 'JPEG', quality=THUMB_Q, optimize=True)
        except Exception as ex:
            print('   [aviso] miniatura falló:', os.path.basename(src_abs), ex)
            return None
    return ('VISOR/thumbs/' + rel_out).replace('\\', '/')


def _to_deg(v):
    try:
        return float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
    except Exception:
        return None


def drone_gps(path):
    try:
        exif = Image.open(path)._getexif()
        if not exif:
            return None
        gps = dt = None
        for tg, val in exif.items():
            n = TAGS.get(tg, tg)
            if n == 'GPSInfo':
                gps = {GPSTAGS.get(k, k): v for k, v in val.items()}
            if n == 'DateTimeOriginal':
                dt = val
        if not gps:
            return None
        lat = _to_deg(gps.get('GPSLatitude')); lon = _to_deg(gps.get('GPSLongitude'))
        if lat is None or lon is None:
            return None
        if gps.get('GPSLatitudeRef') == 'S': lat = -lat
        if gps.get('GPSLongitudeRef') == 'W': lon = -lon
        alt = gps.get('GPSAltitude'); alt = round(float(alt), 1) if alt is not None else None
        fecha = hora = None
        if dt:
            prt = dt.split(' '); fecha = prt[0].replace(':', '-'); hora = prt[1] if len(prt) > 1 else None
        return dict(lon=round(lon, 6), lat=round(lat, 6), alt=alt, fecha=fecha, hora=hora)
    except Exception:
        return None


def track_coords(shp):
    g = gpd.read_file(shp)
    lines = []
    for geom in g.geometry:
        if geom is None:
            continue
        gj = mapping(geom)
        if gj['type'] == 'LineString':
            lines.append([[round(c[1], 6), round(c[0], 6)] for c in gj['coordinates']])
        elif gj['type'] == 'MultiLineString':
            for part in gj['coordinates']:
                lines.append([[round(c[1], 6), round(c[0], 6)] for c in part])
    return lines


def gps_points(shp):
    g = gpd.read_file(shp)
    pts = []
    for i, row in g.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        name = row.get('name'); ele = row.get('ele')
        fecha = hora = None
        if isinstance(name, str):
            if 'T' in name: fecha = name.split('T')[0]
            if '(' in name: hora = name.split('(')[1].split(' ')[0]
        pts.append(dict(lon=round(geom.x, 6), lat=round(geom.y, 6),
                        ele=(round(float(ele), 1) if ele == ele and ele is not None else None),
                        fecha=fecha, hora=hora, idx=i + 1))
    return pts


def cel_photos(shp, site_dir, key):
    g = gpd.read_file(shp)
    cols = {c.lower(): c for c in g.columns}
    cnom = cols.get('nombre'); clon = cols.get('longitude', cols.get('lon'))
    clat = cols.get('latitude', cols.get('lat')); cfe = cols.get('fecha'); cho = cols.get('hora')
    feats = []
    for _, row in g.iterrows():
        nombre = row[cnom] if cnom else None
        geom = row.geometry
        lon = float(row[clon]) if clon else (geom.x if geom is not None else None)
        lat = float(row[clat]) if clat else (geom.y if geom is not None else None)
        if lon is None or lat is None:
            continue
        src = os.path.join(DATOS_DIR, site_dir, 'CELULAR', str(nombre)) if nombre else None
        orig = ('DATOS/' + site_dir + '/CELULAR/' + str(nombre)) if nombre else None
        thumb = make_thumb(src, key + '/cel/' + os.path.splitext(str(nombre))[0] + '.jpg') if (src and os.path.exists(src)) else None
        feats.append(dict(lon=round(lon, 6), lat=round(lat, 6), nombre=str(nombre),
                          fecha=str(row[cfe]) if cfe else None, hora=str(row[cho]) if cho else None,
                          orig=orig, thumb=thumb))
    return feats


def dron_photos(site_dir, key):
    d = os.path.join(DATOS_DIR, site_dir, 'DRON')
    if not os.path.isdir(d):
        return [], []
    jpgs = sorted({p for p in glob.glob(os.path.join(d, '*.JPG')) + glob.glob(os.path.join(d, '*.jpg'))},
                  key=lambda s: s.lower())
    feats = []
    for p in jpgs:
        gg = drone_gps(p)
        if not gg:
            continue
        nombre = os.path.basename(p)
        feats.append(dict(lon=gg['lon'], lat=gg['lat'], alt=gg['alt'], nombre=nombre,
                          fecha=gg['fecha'], hora=gg['hora'],
                          orig='DATOS/' + site_dir + '/DRON/' + nombre,
                          thumb=make_thumb(p, key + '/dron/' + os.path.splitext(nombre)[0] + '.jpg')))
    vids = [os.path.basename(v) for v in glob.glob(os.path.join(d, '*.MP4')) + glob.glob(os.path.join(d, '*.mp4'))]
    return feats, sorted(set(vids))


def build():
    os.makedirs(THUMBS, exist_ok=True)
    data = {}
    print('Leyendo datos desde:', DATOS_DIR)
    for key, s in SITES.items():
        sdir = s['dir']; folder = os.path.join(DATOS_DIR, sdir)
        if not os.path.isdir(folder):
            print('  [SALTADO] %s: no existe la carpeta %s' % (key, sdir))
            continue
        gps_dir = os.path.join(folder, 'GPS'); cel_dir = os.path.join(folder, 'CELULAR')
        f_pts  = find_one(gps_dir, '*PUNTO*.shp', '*punto*.shp')
        f_trk  = find_one(gps_dir, '*TRACK*.shp', '*track*.shp')
        f_foto = find_one(cel_dir, '*COORDENADA*.shp', '*COORDENADA*FOTO*.shp', '*.shp')

        tr  = track_coords(f_trk) if f_trk else []
        pts = gps_points(f_pts) if f_pts else []
        cel = cel_photos(f_foto, sdir, key) if f_foto else []
        dron, vids = dron_photos(sdir, key)
        print('  [%s] %s  -> track:%d vert.(%d seg) | puntos:%d | celular:%d | dron:%d | video:%s'
              % (key, s['meta']['nombre'], sum(len(l) for l in tr), len(tr), len(pts), len(cel), len(dron), vids or '—'))
        data[key] = dict(meta=s['meta'], track=tr, puntos=pts, celular=cel, dron=dron, videos=vids)
    return data


def write_datos_js(data):
    os.makedirs(VISOR, exist_ok=True)
    with open(os.path.join(VISOR, 'datos.js'), 'w', encoding='utf-8') as f:
        f.write('// Datos de la visita técnica - Diapirismo Golfo de Urabá (UNGRD-SCR)\n')
        f.write('const DATOS = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')
    print('  -> VISOR/datos.js actualizado')


def update_html(data):
    if not os.path.exists(HTML):
        print('  [aviso] No se encontró %s; solo se actualizó datos.js' % os.path.basename(HTML))
        return
    html = open(HTML, encoding='utf-8').read()
    block = ('<script>\n// Datos de la visita técnica - Diapirismo Golfo de Urabá (UNGRD-SCR)\n'
             'const DATOS = ' + json.dumps(data, ensure_ascii=False) + ';\n</script>')
    # 1) reemplaza el bloque de datos ya incrustado
    pat_inline = re.compile(r'<script>\s*(?://[^\n]*\n\s*)?const DATOS\b.*?</script>', re.DOTALL)
    # 2) o la referencia externa <script src="VISOR/datos.js">
    pat_src = re.compile(r'<script\s+src=["\']VISOR/datos\.js["\']>\s*</script>')
    if pat_inline.search(html):
        html = pat_inline.sub(lambda m: block, html, count=1)
    elif pat_src.search(html):
        html = pat_src.sub(lambda m: block, html, count=1)
    else:
        print('  [aviso] No se encontró el bloque de datos en el HTML; no se modificó.')
        return
    open(HTML, 'w', encoding='utf-8').write(html)
    print('  -> VISOR_DIAPIRISMO.html actualizado (datos incrustados)')


if __name__ == '__main__':
    print('=' * 70)
    print(' ACTUALIZANDO VISOR — Diapirismo Golfo de Urabá (UNGRD-SCR)')
    print('=' * 70)
    data = build()
    if not data:
        sys.exit('No se encontraron datos. Revisa la carpeta DATOS/ y el diccionario SITES.')
    write_datos_js(data)
    update_html(data)
    print('-' * 70)
    print('LISTO. Abre o recarga VISOR_DIAPIRISMO.html en el navegador.')
    print('=' * 70)
