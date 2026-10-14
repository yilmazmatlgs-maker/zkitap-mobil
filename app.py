# -*- coding: utf-8 -*-
"""
Z Kitap Mobile Engine & Server (v2.0)
Mobil Cihazlar (Telefon & Tablet) İçin Yüksek Hızlı Z-Kitap ve Flip İndirme Motoru
- Altın Karne (Soru / Çözüm / Her İkisi)
- Sınav Dijital (Soru / Çözüm / Her İkisi)
- Fernus Web & Fenomen (141 Yayınevi AES-CBC Şifre Çözücü)
- Supara & FlipBook (Jet Motoru)
- FlipHTML5
- Telefonun Tarayıcısına Doğrudan PDF İndirme & Kütüphane Yönetimi
"""

import os, sys, re, json, time, io, uuid, urllib.request, urllib.error, urllib.parse, ssl, threading, shutil, base64
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except Exception:
    HAS_CRYPTO = False

try:
    import img2pdf
except ImportError:
    img2pdf = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
PDF_DIR = r"c:\Z_Kitap_ve_Flip\PDF"
if not os.path.isdir(PDF_DIR):
    PDF_DIR = os.path.join(BASE_DIR, 'PDF_Mobil')
YAYINEVLERI_DIR = r"c:\Z_Kitap_ve_Flip\yayinevleri"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

def pdf_dizinini_temizle():
    """Bulut sunucusunda disk ve bellek dolmasını önlemek için eski PDF'leri temizler"""
    try:
        if not os.path.isdir(PDF_DIR): return
        files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
        if len(files) > 10:
            files.sort(key=lambda x: os.path.getmtime(x))
            for f in files[:-10]:
                try: os.remove(f)
                except Exception: pass
    except Exception: pass

DEFAULT_UA = 'Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Fernus AES Şifreleme Sabitleri
IV = b'kxk101l0O1l0O1l0'
FALLBACK_MASTER = b'1l0O1l0O1l0O1l0O1l0O1l0O1l0O1l0O'

# Aktif indirme görevleri durum tablosu
TASKS = {}

def turkce_karakter_temizle(s):
    if not s: return ""
    tr_map = str.maketrans("çÇğĞıİöÖşŞüÜ", "cCgGiIoOsSuU")
    return str(s).translate(tr_map)

def extract_page_number(filename):
    m = re.findall(r'\d+', filename)
    return int(m[-1]) if m else 0

def gorsel_uzantisi(b):
    if not b or len(b) < 12: return None
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP': return '.webp'
    if b[:8] == b'\x89PNG\r\n\x1a\n': return '.png'
    if b[:3] == b'\xff\xd8\xff': return '.jpg'
    return None

def fix_url_template(url):
    url = url.strip()
    if '{page}' in url or '{p}' in url: return url
    new_url = re.sub(r'(/pages/)(\d+)(\.(webp|png|jpe?g|gif))', r'\1{page}\3', url, flags=re.IGNORECASE)
    if new_url != url: return new_url
    return re.sub(r'(p-l-|p-|_|/|page)(\d+)(\.(webp|png|jpe?g|gif))', r'\1{page}\3', url, flags=re.IGNORECASE)

# ==============================================================================
# FERNUS & FENOMEN KRİPTO VE YAYINEVİ FONKSİYONLARI
# ==============================================================================

def fernus_web_dec_string(s, key):
    raw = base64.b64decode(s.strip()[::-1])
    cipher = AES.new(key, AES.MODE_CBC, IV)
    pt = cipher.decrypt(raw)
    try: pt = unpad(pt, 16)
    except Exception: pass
    return pt

def fernus_web_aes_dec(raw, key):
    cipher = AES.new(key, AES.MODE_CBC, IV)
    pt = cipher.decrypt(raw)
    try: pt = unpad(pt, 16)
    except Exception: pass
    return pt

def fernus_web_make_key(fernus_code, master):
    k = fernus_code
    if len(k) < 32: k = k + master.decode('latin1')[:32 - len(k)]
    return k.encode('latin1')

def yayinevi_onbellek_al(numara):
    try:
        if not os.path.isdir(YAYINEVLERI_DIR): return None, None
        json_yolu = os.path.join(YAYINEVLERI_DIR, f"{numara}.json")
        if not os.path.isfile(json_yolu): return None, None
        with open(json_yolu, 'r', encoding='utf-8') as f: kayit = json.load(f)
        pub = {'publisher': kayit.get('publisher', '?'), 'pkxkname': kayit.get('pkxkname', ''), 'fernusCode': kayit.get('fernusCode_sifreli', '')}
        fc = kayit.get('fernusCode_gercek', '')
        return pub, (fernus_web_make_key(fc, FALLBACK_MASTER) if fc else None)
    except Exception: return None, None

def fernus_web_url_parse(url):
    url = url.strip()
    sonuc = {'url': url}
    m = re.match(r'(https?://cdn\.fernus\.net/(\d+)/zk/x/b/([^/]+))(?:/p-(?:l-)?(\d+)\.(webp|png|jpg|jpeg|gif))?', url, re.IGNORECASE)
    if m:
        base, numara, kitap = m.group(1), m.group(2), m.group(3)
        uzanti = m.group(5) or 'webp'
        sonuc.update({
            'root_path': f"https://cdn.fernus.net/{numara}/zk/x/p", 'prefix': None, 'numara': numara,
            'kitap_adi': kitap, 'yayinevi': f"Yayinevi_{numara}",
            'sayfa_pattern_soru': f"{base}/p-{{page}}.{uzanti}",
            'sayfa_pattern_cozum': f"{base}/p-l-{{page}}.{uzanti}", 'format': 'cdn'
        })
        return sonuc

    m = re.match(r'(https?://([^/]+)/(?:.*/)?bookszkitapx/([^/]+))(?:/{1,2}p-(?:l-)?(\d+)\.(webp|png|jpg|jpeg|gif))?', url, re.IGNORECASE)
    if m:
        base, domain, kitap = m.group(1), m.group(2), m.group(3)
        uzanti = m.group(5) or 'webp'
        domain_clean = domain.replace('www.', '').split('.')[0].lower()
        prefix = domain_clean
        if 'akillidefter' in domain_clean or 'ari' in domain_clean: prefix = 'ari'
        elif 'fenomen' in domain_clean: prefix = 'fenomen'
        elif 'altin' in domain_clean or 'karma' in domain_clean: prefix = 'altinkarma'
        elif domain_clean.endswith(('okul', 'yayin', 'yayincilik', 'dijital')):
            prefix = re.sub(r'(okul|yayin(?:cilik)?|dijital)$', '', domain_clean)

        slash_delim = '//' if '//p-' in url else '/'
        sonuc.update({
            'root_path': f"http://zkitapxeditor.fernus.net/publishers/{prefix}",
            'alt_root_path': base,
            'prefix': prefix, 'numara': None, 'kitap_adi': kitap, 'yayinevi': prefix.upper(),
            'sayfa_pattern_soru': f"{base}{slash_delim}p-{{page}}.{uzanti}",
            'sayfa_pattern_cozum': f"{base}{slash_delim}p-l-{{page}}.{uzanti}", 'format': 'custom_domain'
        })
        return sonuc
    return None

def fernus_web_publisher_json_al(info):
    anahtar = info.get('numara') or info.get('prefix')
    if anahtar:
        pub, _ = yayinevi_onbellek_al(anahtar)
        if pub: return pub
    if info.get('prefix'):
        for k in [info['prefix'], 'fenomen', 'ari']:
            pub, _ = yayinevi_onbellek_al(k)
            if pub: return pub

    BILINEN = {
        'fenomen': {'publisher': 'FENOMEN', 'pkxkname': 'fenomen', 'fernusCode': '==AB4lf+uPgyIJQMOrbN4uFl'},
        'ari': {'publisher': 'ARI', 'pkxkname': 'ari', 'fernusCode': '==AB0lfg8fW/h/V3Yf70V0Zk'},
        'altinkarma': {'publisher': 'Altın Karma Yayınları', 'pkxkname': 'altinkarma', 'fernusCode': '==QQEgQmMSJrk5Y84mrFcMFP'},
        'oksijen': {'publisher': 'Oksijen Yayınları', 'pkxkname': 'oksijen', 'fernusCode': '==ATEqsLIa7ExwmWmfUYaVQt'},
    }
    prefix = info.get('prefix', '')
    if prefix in BILINEN: return BILINEN[prefix]
    if info.get('numara') in BILINEN: return BILINEN[info['numara']]
    return None

def fernus_web_book_key_al(pub):
    if not pub: return None
    numara_veya_ad = pub.get('numara') or pub.get('pkxkname') or pub.get('prefix')
    if numara_veya_ad:
        _, bk = yayinevi_onbellek_al(numara_veya_ad)
        if bk: return bk
    fs = pub.get('fernusCode')
    if not fs: return None
    try:
        fc = fernus_web_dec_string(fs, FALLBACK_MASTER).decode('utf-8')
        return fernus_web_make_key(fc, FALLBACK_MASTER)
    except Exception: return None

def fernus_indir_ve_coz_sayfa(url, hedef_yol, book_key):
    headers = {'User-Agent': DEFAULT_UA, 'Referer': 'https://zkitapx.fernus.net/'}
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                if r.status == 200:
                    raw = bytearray(r.read())
                    if len(raw) > 500:
                        pt = bytes(raw)
                        if gorsel_uzantisi(pt) is None:
                            tmp_raw = bytearray(raw)
                            for i in range(min(100, len(tmp_raw))): tmp_raw[i] = (256 - tmp_raw[i]) & 0xFF
                            if gorsel_uzantisi(bytes(tmp_raw)) is not None:
                                pt = bytes(tmp_raw)
                            elif book_key:
                                try:
                                    dec = fernus_web_aes_dec(bytes(raw), book_key)
                                    if gorsel_uzantisi(dec) is not None: pt = dec
                                except Exception: pass
                        ext = gorsel_uzantisi(pt)
                        if ext:
                            final_dest = hedef_yol if hedef_yol.endswith(ext) else hedef_yol + ext
                            with open(final_dest, 'wb') as f: f.write(pt)
                            return True
        except Exception:
            time.sleep(0.2)
    return False

def dijital_indir_sayfa(url, hedef_yol, referer=None, max_deneme=3):
    headers = {'User-Agent': DEFAULT_UA, 'Accept': 'image/*,*/*;q=0.8'}
    if referer: headers['Referer'] = referer
    for deneme in range(1, max_deneme + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as r:
                if r.status == 200:
                    data = r.read()
                    if len(data) > 500:
                        ext = gorsel_uzantisi(data) or '.jpg'
                        base_path = os.path.splitext(hedef_yol)[0]
                        final_path = base_path + ext
                        with open(final_path, 'wb') as f: f.write(data)
                        return True
        except urllib.error.HTTPError as he:
            if he.code in (404, 500): return False
        except Exception:
            time.sleep(0.3)
    return False

def gorsellerden_pdf_yap(gorsel_yollari, cikti_pdf_yolu, webp_kalite=100):
    if not gorsel_yollari:
        return False

    import gc

    # 1. Aşama: img2pdf ile diskteki dosya yollarından doğrudan akış (RAM: 0.3 MB, Süre: 1-2 sn)
    if img2pdf:
        try:
            with open(cikti_pdf_yolu, 'wb') as f:
                img2pdf.convert(gorsel_yollari, outputstream=f)
            gc.collect()
            pdf_dizinini_temizle()
            return True
        except Exception as e:
            print(f"img2pdf doğrudan dönüştürme uyarısı: {e}, uyumluluk moduna geçiliyor...")

    # 2. Aşama: Format uyuşmazlığı varsa (örn. özel PNG/alfa/bozuk meta),
    # sayfaları TEK TEK diske JPEG olarak normalize et (Belleği şişirmeden, RAM < 20MB)
    temp_conv_dir = os.path.join(os.path.dirname(cikti_pdf_yolu), f"conv_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_conv_dir, exist_ok=True)
    normalized_paths = []
    try:
        q = 95 if int(webp_kalite) >= 98 else int(webp_kalite)
        for idx, yol in enumerate(gorsel_yollari):
            target_jpg = os.path.join(temp_conv_dir, f"p_{idx:04d}.jpg")
            try:
                with Image.open(yol) as im:
                    if im.mode != 'RGB':
                        im = im.convert('RGB')
                    im.save(target_jpg, 'JPEG', quality=q, optimize=True)
                normalized_paths.append(target_jpg)
            except Exception as ex_norm:
                print(f"Sayfa normalize hatası ({yol}): {ex_norm}")
            if idx % 25 == 0:
                gc.collect()

        if normalized_paths and img2pdf:
            try:
                with open(cikti_pdf_yolu, 'wb') as f:
                    img2pdf.convert(normalized_paths, outputstream=f)
                pdf_dizinini_temizle()
                return True
            except Exception as e2:
                print(f"img2pdf normalize sonrası hata: {e2}")

        # 3. Aşama: Pillow Fallback (Son çare)
        if normalized_paths:
            try:
                first_img = Image.open(normalized_paths[0])
                other_imgs = [Image.open(p) for p in normalized_paths[1:]]
                first_img.save(cikti_pdf_yolu, "PDF", resolution=150.0, save_all=True, append_images=other_imgs)
                first_img.close()
                for im in other_imgs:
                    im.close()
                del other_imgs
                gc.collect()
                pdf_dizinini_temizle()
                return True
            except Exception as e3:
                print(f"Pillow fallback hatası: {e3}")
    finally:
        shutil.rmtree(temp_conv_dir, ignore_errors=True)
        gc.collect()

    return False


# ==============================================================================
# ANALİZ SERVİSLERİ
# ==============================================================================

def analiz_et(girdi_url):
    girdi = girdi_url.strip()

    # 1. Altın Karne
    if 'altinkarne.com' in girdi.lower() or (girdi.isdigit() and len(girdi) < 6):
        m = re.search(r'book-app/(\d+)', girdi) or re.search(r'bookId=(\d+)', girdi)
        book_id = m.group(1) if m else (girdi if girdi.isdigit() else None)
        if not book_id: raise ValueError("Altın Karne kitap ID tespit edilemedi.")

        api_url = f"https://www.altinkarne.com/bookapp/GetBook?bookId={book_id}"
        req = urllib.request.Request(api_url, headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            data = json.loads(r.read().decode('utf-8'))

        b = data.get('books', {}).get('book', {})
        baslik = b.get('bookName') or f"AltinKarne_{book_id}"
        has_cozum = bool(b.get('hasCozum', True))
        items = b.get('items') or b.get('page') or []
        sayfalar = []

        if isinstance(items, list) and items:
            total_pages = len(items)
            for item in items:
                cnt = item.get('content', {}) if isinstance(item, dict) else {}
                p_num = int(cnt.get('page') or cnt.get('orginalPageNumber') or len(sayfalar) + 1)
                s_url = cnt.get('url') or f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page={p_num}.jpg"
                c_url = cnt.get('cozumUrl') or f"https://www.altinkarne.com/bookapp/GetCozumImage?bookId={book_id}&page={p_num}.jpg"
                sayfalar.append({'page': p_num, 'soru_url': s_url, 'cozum_url': c_url})
        else:
            p_val = b.get('page')
            total_pages = int(p_val) if isinstance(p_val, (int, str)) and str(p_val).isdigit() else 240
            for p_num in range(1, total_pages + 1):
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page={p_num}.jpg",
                    'cozum_url': f"https://www.altinkarne.com/bookapp/GetCozumImage?bookId={book_id}&page={p_num}.jpg"
                })

        kapak_url = f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page=1.jpg"
        return {
            'platform': 'ALTIN_KARNE',
            'platform_label': 'Altın Karne',
            'book_id': book_id,
            'title': baslik,
            'pages_count': total_pages,
            'has_solution': has_cozum,
            'cover_url': kapak_url,
            'pages': sayfalar
        }

    # 2. Sınav Dijital
    uuid_match = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', girdi)
    if 'sinavdijital.com' in girdi.lower() or uuid_match:
        uuid_str = uuid_match.group(0) if uuid_match else None
        if not uuid_str: raise ValueError("Sınav Dijital belge kodu tespit edilemedi.")

        title = f"SinavDijital_{uuid_str[:8]}"
        try:
            req = urllib.request.Request(f"https://www.sinavdijital.com/api/documents/{uuid_str}/", headers={'User-Agent': DEFAULT_UA})
            with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as r:
                doc = json.loads(r.read().decode('utf-8')).get('document', {})
                if doc.get('title'): title = doc['title']
        except Exception: pass

        req = urllib.request.Request(f"https://www.sinavdijital.com/api/document/{uuid_str}/pages/", headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            pages_data = json.loads(r.read().decode('utf-8')).get('pages', [])

        sayfalar = []
        if pages_data:
            total_pages = len(pages_data)
            for p_item in pages_data:
                p_num = int(p_item.get('page_number', 1))
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page={p_num}.png",
                    'cozum_url': f"https://www.sinavdijital.com/api/bookapp/GetCozumImage?bookId={uuid_str}&page={p_num}.png"
                })
        else:
            total_pages = 60
            for p_num in range(1, 61):
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page={p_num}.png",
                    'cozum_url': f"https://www.sinavdijital.com/api/bookapp/GetCozumImage?bookId={uuid_str}&page={p_num}.png"
                })

        kapak_url = f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page=1.png"
        return {
            'platform': 'SINAV_DIJITAL',
            'platform_label': 'Sınav Dijital',
            'book_id': uuid_str,
            'title': title,
            'pages_count': total_pages,
            'has_solution': True,
            'cover_url': kapak_url,
            'pages': sayfalar
        }

    # 3. Fernus & Fenomen Web Z-Kitap
    if any(k in girdi.lower() for k in ('cdn.fernus.net', 'bookszkitapx', 'akillidefter.com.tr', 'fenomenokul.com', 'zkitapx')):
        info = fernus_web_url_parse(girdi)
        if not info: raise ValueError("Fernus Web URL formatı tanınamadı.")
        pub = fernus_web_publisher_json_al(info)
        book_key = fernus_web_book_key_al(pub)

        title = info.get('kitap_adi', 'Fernus_Kitap')
        sayfalar = []
        for p in range(1, 401):
            s_u = info['sayfa_pattern_soru'].replace('{page}', str(p))
            c_u = info['sayfa_pattern_cozum'].replace('{page}', str(p))
            sayfalar.append({'page': p, 'soru_url': s_u, 'cozum_url': c_u})

        return {
            'platform': 'FERNUS_WEB',
            'platform_label': f"Fernus Web ({info.get('yayinevi', 'Z-Kitap')})",
            'book_id': info.get('kitap_adi', 'fernus'),
            'title': title,
            'pages_count': len(sayfalar),
            'has_solution': True,
            'cover_url': '',
            'book_key_hex': book_key.hex() if book_key else '',
            'pages': sayfalar
        }

    # 4. SmartBook / Newton / Nitelik / Supara (Obro API)
    m_smart = re.search(r'(?:smartBook/|guid=|bookId=|book_id=)([a-zA-Z0-9\-]+)', girdi, re.IGNORECASE)
    is_smart = any(k in girdi.lower() for k in ('smartbook', 'newtondijital', 'nitelik', 'supara', 'viewbook')) or m_smart
    if is_smart and ('fliphtml5' not in girdi.lower()):
        parsed = urllib.parse.urlparse(girdi)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        book_id = m_smart.group(1) if m_smart else "370"
        api_url = f"{base_url}/api/smartbook/SbPublicGuess/GetSmartBook?bookId={book_id}&includePageItems=true"

        req = urllib.request.Request(api_url, headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            data = json.loads(r.read().decode('utf-8'))

        title = data.get('title') or data.get('name') or f"SmartBook_{book_id}"
        pages = []
        for idx, p in enumerate(data.get('pages', []), 1):
            if p.get('pageImageUrl'):
                u = p['pageImageUrl']
                u_full = u if u.startswith('http') else f"{base_url}/{u.lstrip('/')}"
                pages.append({'page': idx, 'soru_url': u_full, 'cozum_url': None})

        kapak = pages[0]['soru_url'] if pages else ""
        label = "Newton SmartBook" if "newton" in girdi.lower() else ("Nitelik SmartBook" if "nitelik" in girdi.lower() else "Supara FlipBook")
        return {
            'platform': 'SUPARA_FLIP',
            'platform_label': label,
            'book_id': str(book_id),
            'title': title,
            'pages_count': len(pages),
            'has_solution': False,
            'cover_url': kapak,
            'pages': pages
        }

    # 5. İmpark Web Z-Kitap
    if any(k in girdi.lower() for k in ('/pages/', '/uploads/', 'impark', 'ozdebirdijital', 'yargidersarkadasim')):
        fixed_url = fix_url_template(girdi)
        clean_no_query = girdi.split('?')[0].rstrip('/')
        parcalar = [p for p in clean_no_query.split('/') if p and not p.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.gif'))]
        kitap_adi = f"Impark_{parcalar[-1]}" if parcalar else "Impark_Kitap"
        pages = []
        for p in range(1, 401):
            p_url = fixed_url.replace('{page}', str(p)).replace('{p}', str(p))
            pages.append({'page': p, 'soru_url': p_url, 'cozum_url': None})
        return {
            'platform': 'IMPARK_WEB',
            'platform_label': 'İmpark Web',
            'book_id': kitap_adi,
            'title': kitap_adi,
            'pages_count': 400,
            'has_solution': False,
            'cover_url': pages[0]['soru_url'] if pages else '',
            'pages': pages
        }

    # 6. FlipHTML5 (Jet Motoru - Otomatik Sayfa ve Şifre Çözücü)
    if 'fliphtml5.com' in girdi.lower():
        m = re.search(r'fliphtml5\.com/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)', girdi)
        if m:
            u_code, b_code = m.group(1), m.group(2)
            book_url = f"https://online.fliphtml5.com/{u_code}/{b_code}/"
            title = f"FlipHTML5_{u_code}_{b_code}"
            pages = []

            # 1. Aşama: Headless Chrome ile dinamik/WASM ile şifrelenmiş sayfa listesini çöz
            driver = None
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options

                chrome_opts = Options()
                chrome_opts.add_argument('--headless=new')
                chrome_opts.add_argument('--no-sandbox')
                chrome_opts.add_argument('--disable-dev-shm-usage')
                chrome_opts.add_argument('--disable-gpu')
                chrome_opts.add_argument(f'user-agent={DEFAULT_UA}')

                driver = webdriver.Chrome(options=chrome_opts)
                driver.get(book_url)
                time.sleep(3)

                js_extract = '''
                var urls = [];
                var base = (window.bookConfig && window.bookConfig.bookBaseURL) || location.href.replace(/#.*$/, '');
                if(!base.endsWith('/')) base += '/';

                var pList = null;
                if (Array.isArray(window.fliphtml5_pages)) pList = window.fliphtml5_pages;
                else if (window.bookConfig && Array.isArray(window.bookConfig.pages)) pList = window.bookConfig.pages;
                else if (window.htmlConfig && Array.isArray(window.htmlConfig.pageEditor)) pList = window.htmlConfig.pageEditor;

                if (pList && pList.length > 0) {
                    for(var i=0; i<pList.length; i++) {
                        var p = pList[i];
                        var u = null;
                        if(typeof p === 'string') u = p;
                        else if(typeof p === 'object' && p !== null) u = p.n || p.large || p.normal || p.src || p.l || p.ptf;
                        if(Array.isArray(u)) u = u[0];
                        if(u) {
                            if(u.startsWith('http')) urls.push(u);
                            else {
                                var rel = u.replace(/\\\\/g, '/');
                                while(rel.startsWith('./')) rel = rel.substring(2);
                                if(rel.startsWith('/')) rel = rel.substring(1);
                                urls.push(base + rel);
                            }
                        }
                    }
                }
                var t = document.title || '';
                return {title: t, urls: urls};
                '''

                res = driver.execute_script(js_extract)
                if res:
                    raw_title = res.get('title', '')
                    if raw_title and 'Just a moment' not in raw_title and raw_title.strip() != 'FlipHTML5':
                        title = re.sub(r'[\\/*?:"<>|]', '_', raw_title).strip()

                    found_urls = res.get('urls', [])
                    for idx, u in enumerate(found_urls, 1):
                        pages.append({'page': idx, 'soru_url': u, 'cozum_url': None})
            except Exception as ex:
                print(f"FlipHTML5 Headless Çözüm Hatası: {ex}")
            finally:
                if driver:
                    try: driver.quit()
                    except Exception: pass

            # 2. Aşama Fallback: Headless sayfaları çekemediyse olası formatları yokla
            if not pages:
                candidates = [
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/1.jpg",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/mobile/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/mobile/1.jpg",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/1.jpg"
                ]
                working_tpl = None
                for cand in candidates:
                    try:
                        req_c = urllib.request.Request(cand, headers={'User-Agent': DEFAULT_UA, 'Referer': book_url})
                        with urllib.request.urlopen(req_c, timeout=3, context=SSL_CTX) as rc:
                            if rc.status == 200 and len(rc.read()) > 500:
                                working_tpl = cand.replace('/1.', '/{page}.')
                                break
                    except Exception:
                        pass

                if not working_tpl:
                    working_tpl = f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/{{page}}.jpg"

                for idx in range(1, 401):
                    pages.append({'page': idx, 'soru_url': working_tpl.replace('{page}', str(idx)), 'cozum_url': None})

            kapak = pages[0]['soru_url'] if pages else ""
            return {
                'platform': 'FLIPHTML5',
                'platform_label': 'FlipHTML5 Jet',
                'book_id': f"{u_code}_{b_code}",
                'title': title,
                'pages_count': len(pages),
                'has_solution': False,
                'cover_url': kapak,
                'referer': book_url,
                'pages': pages
            }

    raise ValueError("Girilen link desteklenen bir formatta değil. Fernus, Newton, İmpark, Supara, FlipHTML5, Altın Karne veya Sınav Dijital linki giriniz.")

# ==============================================================================
# ARKA PLAN İNDİRME MOTORU
# ==============================================================================

def benzersiz_pdf_adi(dizin, baslik_temiz, son_ek=""):
    ek = f" - {son_ek}" if son_ek else ""
    ad = f"[Mobil PDF] {baslik_temiz}{ek}" if not baslik_temiz.startswith("[Mobil PDF]") else f"{baslik_temiz}{ek}"
    hedef = f"{ad}.pdf"
    sayac = 1
    while os.path.exists(os.path.join(dizin, hedef)):
        sayac += 1
        hedef = f"{ad} ({sayac}).pdf"
    return hedef

def indirme_gorevi_baslat(task_id, kitap_verisi, mod=1, webp_kalite=100):
    TASKS[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': 'İndirme hazırlanıyor...',
        'completed': 0,
        'total': 0,
        'pdf_files': []
    }

    def run():
        try:
            pages = kitap_verisi['pages']
            temiz_baslik = re.sub(r'[\\/*?:"<>|]', '_', str(kitap_verisi['title'])).strip()[:100]
            temp_dir = os.path.join(PDF_DIR, f"temp_{uuid.uuid4().hex[:8]}")
            os.makedirs(temp_dir, exist_ok=True)

            ref = "https://www.altinkarne.com/" if kitap_verisi['platform'] == 'ALTIN_KARNE' else None
            if kitap_verisi['platform'] == 'SINAV_DIJITAL': ref = "https://www.sinavdijital.com/"
            if kitap_verisi['platform'] == 'FLIPHTML5': ref = kitap_verisi.get('referer') or "https://online.fliphtml5.com/"

            is_fernus = kitap_verisi['platform'] == 'FERNUS_WEB'
            is_impark = kitap_verisi['platform'] == 'IMPARK_WEB'
            bk_bytes = bytes.fromhex(kitap_verisi.get('book_key_hex', '')) if is_fernus and kitap_verisi.get('book_key_hex') else None

            tasks = []
            if mod in (1, 3):
                for p in pages:
                    dest = os.path.join(temp_dir, f"s_{p['page']:04d}")
                    tasks.append(('SORU', p['page'], p['soru_url'], dest))
            if mod in (2, 3) and kitap_verisi.get('has_solution'):
                for p in pages:
                    if p.get('cozum_url'):
                        dest = os.path.join(temp_dir, f"c_{p['page']:04d}")
                        tasks.append(('COZUM', p['page'], p['cozum_url'], dest))

            toplam = len(tasks)
            TASKS[task_id]['total'] = toplam
            tamamlanan = 0

            with ThreadPoolExecutor(max_workers=8) as ex:
                if is_fernus or is_impark:
                    futs = {ex.submit(fernus_indir_ve_coz_sayfa, t[2], t[3], bk_bytes): t for t in tasks}
                else:
                    futs = {ex.submit(dijital_indir_sayfa, t[2], t[3], ref): t for t in tasks}

                for f in as_completed(futs):
                    tamamlanan += 1
                    yuzde = int((tamamlanan / toplam) * 85)
                    TASKS[task_id]['completed'] = tamamlanan
                    TASKS[task_id]['progress'] = yuzde
                    TASKS[task_id]['message'] = f"Sayfalar işleniyor... ({tamamlanan}/{toplam})"

            TASKS[task_id]['message'] = "Yüksek kaliteli PDF oluşturuluyor..."
            TASKS[task_id]['progress'] = 90
            uretilen_pdfler = []

            def _is_valid_file(fp):
                try:
                    with open(fp, 'rb') as f:
                        return gorsel_uzantisi(f.read(16)) is not None
                except Exception:
                    return False

            all_files = os.listdir(temp_dir)
            if mod in (1, 3):
                soru_img = [os.path.join(temp_dir, fn) for fn in all_files if fn.startswith('s_') and _is_valid_file(os.path.join(temp_dir, fn))]
                soru_img.sort(key=lambda x: extract_page_number(os.path.basename(x)))
                if soru_img:
                    out_name = benzersiz_pdf_adi(PDF_DIR, temiz_baslik)
                    out_pdf = os.path.join(PDF_DIR, out_name)
                    if gorsellerden_pdf_yap(soru_img, out_pdf, webp_kalite=webp_kalite):
                        uretilen_pdfler.append(out_name)

            if mod in (2, 3) and kitap_verisi.get('has_solution'):
                cozum_img = [os.path.join(temp_dir, fn) for fn in all_files if fn.startswith('c_') and _is_valid_file(os.path.join(temp_dir, fn))]
                cozum_img.sort(key=lambda x: extract_page_number(os.path.basename(x)))
                if cozum_img:
                    out_cozum_name = benzersiz_pdf_adi(PDF_DIR, temiz_baslik, son_ek="Çözümler")
                    out_cozum_pdf = os.path.join(PDF_DIR, out_cozum_name)
                    if gorsellerden_pdf_yap(cozum_img, out_cozum_pdf, webp_kalite=webp_kalite):
                        uretilen_pdfler.append(out_cozum_name)

            shutil.rmtree(temp_dir, ignore_errors=True)

            if uretilen_pdfler:
                refresh_short_map()
                TASKS[task_id]['status'] = 'completed'
                TASKS[task_id]['progress'] = 100
                TASKS[task_id]['message'] = f"İşlem Başarılı! {len(uretilen_pdfler)} adet PDF hazırlandı."
                TASKS[task_id]['pdf_files'] = uretilen_pdfler
                TASKS[task_id]['pdf_files_info'] = [
                    {
                        'name': fn,
                        'url': f"/pdf/{urllib.parse.quote(fn)}",
                        'short_url': f"/d/{SHORT_REVERSE.get(fn, '1')}"
                    }
                    for fn in uretilen_pdfler
                ]
            else:
                TASKS[task_id]['status'] = 'failed'
                TASKS[task_id]['message'] = "Sayfalar indirilemedi veya PDF oluşturulamadı."

        except Exception as e:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['message'] = f"Hata: {str(e)}"

    t = threading.Thread(target=run, daemon=True)
    t.start()

def toplu_indirme_gorevi_baslat(task_id, kitap_listesi, mod=1, webp_kalite=100):
    TASKS[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': f"Toplu indirme başlıyor (Toplam {len(kitap_listesi)} kitap)...",
        'completed': 0,
        'total': len(kitap_listesi),
        'pdf_files': [],
        'pdf_files_info': []
    }

    def run():
        total_books = len(kitap_listesi)
        all_produced = []
        for i, b_data in enumerate(kitap_listesi, 1):
            sub_id = f"{task_id}_{i}"
            b_title = b_data.get('title', 'Kitap')
            clean_b_title = b_title[:32] + '...' if len(b_title) > 32 else b_title
            TASKS[task_id]['message'] = f"[{i}/{total_books}] {clean_b_title} başlatılıyor..."
            TASKS[task_id]['progress'] = max(1, int(((i - 1) / total_books) * 95))

            indirme_gorevi_baslat(sub_id, b_data, mod=mod, webp_kalite=webp_kalite)

            while TASKS.get(sub_id, {}).get('status') == 'running':
                st = TASKS.get(sub_id, {})
                sub_prog = st.get('progress', 0)
                sub_comp = st.get('completed', 0)
                sub_tot = st.get('total', 0)
                sub_msg = st.get('message', '')

                # Kitabın kendi içindeki sayfa ilerlemesini toplu ilerlemeye yansıt
                overall_prog = int(((i - 1) + (sub_prog / 100.0)) / total_books * 95)
                TASKS[task_id]['progress'] = max(1, min(95, overall_prog))
                TASKS[task_id]['completed'] = sub_comp
                TASKS[task_id]['total'] = sub_tot
                TASKS[task_id]['message'] = f"[{i}/{total_books}] {clean_b_title}: {sub_msg}"
                time.sleep(0.4)

            sub_task = TASKS.get(sub_id, {})
            if sub_task.get('status') == 'completed':
                for fn in sub_task.get('pdf_files', []):
                    if fn not in all_produced:
                        all_produced.append(fn)
            else:
                print(f"[Toplu İndirme] Alt görev {sub_id} ({b_title}) tamamlanamadı: {sub_task.get('message')}")

            TASKS[task_id]['pdf_files'] = list(all_produced)

        if all_produced:
            refresh_short_map()
            TASKS[task_id]['status'] = 'completed'
            TASKS[task_id]['progress'] = 100
            TASKS[task_id]['message'] = f"Toplu İşlem Tamamlandı! {len(all_produced)} adet PDF hazırlandı."
            TASKS[task_id]['pdf_files'] = all_produced
            TASKS[task_id]['pdf_files_info'] = [
                {
                    'name': fn,
                    'url': f"/pdf/{urllib.parse.quote(fn)}",
                    'short_url': f"/d/{SHORT_REVERSE.get(fn, '1')}"
                }
                for fn in all_produced
            ]
        else:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['progress'] = 0
            TASKS[task_id]['message'] = "Toplu indirmedeki hiçbir kitap PDF'e dönüştürülemedi."

    t = threading.Thread(target=run, daemon=True)
    t.start()

# ==============================================================================
# HTTP SUNUCU İŞLEYİCİSİ
# ==============================================================================

SHORT_MAP = {}
SHORT_REVERSE = {}

def refresh_short_map():
    global SHORT_MAP, SHORT_REVERSE
    SHORT_MAP.clear()
    SHORT_REVERSE.clear()
    if os.path.isdir(PDF_DIR):
        files = [fn for fn in sorted(os.listdir(PDF_DIR)) if fn.lower().endswith('.pdf')]
        for idx, fn in enumerate(files, 1):
            sid = str(idx)
            SHORT_MAP[sid] = fn
            SHORT_REVERSE[fn] = sid

class MobileServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/library':
            refresh_short_map()
            files = []
            if os.path.isdir(PDF_DIR):
                for fn in os.listdir(PDF_DIR):
                    if fn.lower().endswith('.pdf'):
                        fp = os.path.join(PDF_DIR, fn)
                        sz = os.path.getsize(fp) / (1024 * 1024)
                        mtime = os.path.getmtime(fp)
                        sid = SHORT_REVERSE.get(fn, "1")
                        files.append({
                            'name': fn,
                            'id': sid,
                            'size_mb': f"{sz:.1f} MB",
                            'date': time.strftime("%d.%m.%Y %H:%M", time.localtime(mtime)),
                            'url': f"/pdf/{urllib.parse.quote(fn)}",
                            'short_url': f"/d/{sid}"
                        })
            files.sort(key=lambda x: x['date'], reverse=True)
            self._json_response({'success': True, 'files': files})
            return

        if path == '/api/progress':
            qs = urllib.parse.parse_qs(parsed.query)
            tid = qs.get('id', [None])[0]
            if tid and tid in TASKS:
                self._json_response({'success': True, 'task': TASKS[tid]})
            else:
                self._json_response({'success': False, 'message': 'Görev bulunamadı'})
            return

        if path.startswith('/d/'):
            sid = path[3:].split('?')[0].split('/')[0]
            refresh_short_map()
            fname = SHORT_MAP.get(sid)
            if fname:
                fp = os.path.join(PDF_DIR, fname)
                if os.path.isfile(fp):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/pdf')
                    safe_ascii = turkce_karakter_temizle(fname).encode('ascii', 'ignore').decode('ascii') or "kitap.pdf"
                    encoded_utf8 = urllib.parse.quote(fname)
                    self.send_header('Content-Disposition', f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_utf8}')
                    self.send_header('Content-Length', str(os.path.getsize(fp)))
                    self.end_headers()
                    with open(fp, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
            self.send_error(404, "Kisa link bulunamadi")
            return

        if path == '/api/download_pdf' or path.startswith('/pdf/'):
            fname = None
            if path.startswith('/pdf/'):
                fname = urllib.parse.unquote(path[5:])
            else:
                qs = urllib.parse.parse_qs(parsed.query)
                fname = qs.get('name', [None])[0]

            if fname:
                fp = os.path.join(PDF_DIR, os.path.basename(fname))
                if os.path.isfile(fp):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/pdf')
                    safe_ascii = turkce_karakter_temizle(os.path.basename(fname)).encode('ascii', 'ignore').decode('ascii') or "kitap.pdf"
                    encoded_utf8 = urllib.parse.quote(os.path.basename(fname))
                    self.send_header('Content-Disposition', f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_utf8}')
                    self.send_header('Content-Length', str(os.path.getsize(fp)))
                    self.end_headers()
                    with open(fp, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
            self.send_error(404, "Dosya bulunamadi")
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
        data = json.loads(body) if body else {}

        if parsed.path == '/api/analyze':
            raw_url = data.get('url', '').strip()
            if not raw_url:
                self._json_response({'success': False, 'message': 'Lütfen geçerli bir link veya ID girin.'}, status=400)
                return

            # Tüm http(s) linklerini regex ile metinden çek (boşluk, virgül, satır sonu fark etmeksizin)
            found_urls = re.findall(r'https?://[^\s,;"\'<>]+', raw_url)
            if not found_urls:
                # URL formatında değilse satırlara, boşluklara veya virgüllere böl (örn. sadece kitap ID'leri girilmişse: 647 648)
                tokens = [s.strip() for s in re.split(r'[\r\n,;\s]+', raw_url) if s.strip() and not s.strip().startswith('#')]
            else:
                tokens = found_urls

            # Tekilleştir
            seen = set()
            unique_tokens = []
            for t in tokens:
                if t not in seen:
                    seen.add(t)
                    unique_tokens.append(t)

            if len(unique_tokens) > 1:
                # Toplu Link Analizi
                books = []
                errors = []
                for u in unique_tokens:
                    try:
                        b = analiz_et(u)
                        books.append(b)
                    except Exception as e:
                        errors.append(f"{u[:40]}...: {str(e)}")
                if not books:
                    self._json_response({'success': False, 'message': f"Hiçbir link çözülemedi:\n" + "\n".join(errors)}, status=400)
                    return
                self._json_response({'success': True, 'is_batch': True, 'books': books, 'errors': errors})
                return
            else:
                target_url = unique_tokens[0] if unique_tokens else raw_url
                try:
                    res = analiz_et(target_url)
                    self._json_response({'success': True, 'is_batch': False, 'data': res})
                except Exception as e:
                    self._json_response({'success': False, 'message': str(e)}, status=400)
                return

        if parsed.path == '/api/start_download':
            kitap_data = data.get('book_data')
            mod = int(data.get('mod', 1))
            kalite = int(data.get('quality', 100))
            if not kitap_data:
                self._json_response({'success': False, 'message': 'Kitap verisi eksik.'}, status=400)
                return
            tid = str(uuid.uuid4())
            indirme_gorevi_baslat(tid, kitap_data, mod=mod, webp_kalite=kalite)
            self._json_response({'success': True, 'task_id': tid})
            return

        if parsed.path == '/api/start_batch_download':
            books = data.get('books', [])
            mod = int(data.get('mod', 1))
            kalite = int(data.get('quality', 100))
            if not books:
                self._json_response({'success': False, 'message': 'Kitap listesi eksik.'}, status=400)
                return
            batch_id = str(uuid.uuid4())
            toplu_indirme_gorevi_baslat(batch_id, books, mod=mod, webp_kalite=kalite)
            self._json_response({'success': True, 'task_id': batch_id})
            return

        if parsed.path == '/api/delete_pdf':
            fname = data.get('name')
            if fname:
                fp = os.path.join(PDF_DIR, os.path.basename(fname))
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                        refresh_short_map()
                        self._json_response({'success': True})
                        return
                    except Exception as e:
                        self._json_response({'success': False, 'message': str(e)}, status=500)
                        return
            self._json_response({'success': False, 'message': 'Dosya bulunamadı'}, status=404)
            return

        self.send_error(404, "Endpoint bulunamadi")

    def _json_response(self, obj, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode('utf-8'))

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def run_port_listener(p):
    try:
        server = ThreadingHTTPServer(('0.0.0.0', p), MobileServerHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Port {p} dinlenemedi: {e}")

def main():
    import sys
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    local_ip = get_local_ip()
    main_port = int(os.environ.get('PORT', 5050))

    # Port 80'i sadece yerel Windows ortamında ve ana port farklıysa dene
    if main_port != 80 and not os.environ.get('PORT'):
        t80 = threading.Thread(target=run_port_listener, args=(80,), daemon=True)
        t80.start()

    print("\n" + "="*60)
    print(" [OK] Z KITAP MOBIL SUNUCUSU BASLATILDI (v2.7)")
    print("="*60)
    print(f" * Ana Servis Portu:     http://{local_ip}:{main_port}")
    print(f" * Bilgisayardan Erisim: http://localhost:{main_port}")
    print("="*60 + "\n")

    # Ana servisi calistir
    run_port_listener(main_port)

if __name__ == '__main__':
    main()
