// Z Kitap Mobil - Frontend Mantığı (v2.0)

let activeDijitalData = null;
let activeDijitalMod = 1;
let activeDijitalBatchBooks = [];
let activeWebData = null;
let activeWebMod = 1;
let activeBatchBooks = [];
let activeFlipData = null;
let activeFlipBatchBooks = [];
let activeQuality = 100;

function setQuality(val, btn) {
  activeQuality = val;
  const parent = btn.parentElement;
  if (parent) {
    parent.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
  }
  btn.classList.add('active');
}

// Devam eden indirmeleri takip eden kilit mekanizması (çift tıklamayı ve paralel indirmeyi önler)
const downloadingState = {
  dijital: false,
  web: false,
  flip: false
};

// Yalnızca giriş kutusunun içeriğini temizler (Kartları ve ilerleme çubuğunu ASLA kapatmaz)
function clearInputBox(id) {
  const el = document.getElementById(id);
  if (el) {
    el.value = '';
    el.focus();
  }
}

// Kullanıcı çöp kutusuna bastığında sekmeyi sıfırlar (indirme devam ediyorsa korur)
function resetTab(prefix) {
  if (downloadingState[prefix]) {
    alert('Şu anda indirme devam ediyor, lütfen bitmesini bekleyiniz.');
    return;
  }
  const el = document.getElementById(`${prefix}-url`);
  if (el) el.value = '';

  const s = document.getElementById(`${prefix}-sonuc`);
  const sb = document.getElementById(`${prefix}-batch-sonuc`);
  const p = document.getElementById(`${prefix}-progress`);
  const act = document.getElementById(`${prefix}-tamam-actions`);
  if (s) s.style.display = 'none';
  if (sb) sb.style.display = 'none';
  if (p) p.style.display = 'none';
  if (act) { act.style.display = 'none'; act.innerHTML = ''; }

  if (prefix === 'dijital') {
    activeDijitalData = null;
    activeDijitalBatchBooks = [];
  } else if (prefix === 'web') {
    activeWebData = null;
    activeBatchBooks = [];
  } else if (prefix === 'flip') {
    activeFlipData = null;
    activeFlipBatchBooks = [];
  }
}

// İndirilen dosyaların telefon hafızasında takibi (sayfa yenilense de hatırlar)
let downloadedFiles = new Set();
try {
  const saved = localStorage.getItem('zk_downloaded_pdfs');
  if (saved) downloadedFiles = new Set(JSON.parse(saved));
} catch (e) {}

function markFileDownloaded(fileName) {
  downloadedFiles.add(fileName);
  try {
    localStorage.setItem('zk_downloaded_pdfs', JSON.stringify([...downloadedFiles]));
  } catch (e) {}
}

// Service Worker Kaydı (PWA)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

// Sekme Geçişi (Hem Üst Hap Butonları Hem Alt Barı Eşzamanlar)
function switchTab(tabId, el) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.top-pill').forEach(p => p.classList.remove('active'));

  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add('active');

  // Alt bar öğesini aktifleştir
  const bottomItem = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (bottomItem) bottomItem.classList.add('active');

  // Üst pill öğesini aktifleştir
  const pillIndex = { 'tab-dijital': 0, 'tab-web': 1, 'tab-flip': 2, 'tab-library': 3 }[tabId];
  const allPills = document.querySelectorAll('.top-pill');
  if (pillIndex !== undefined && allPills[pillIndex]) {
    allPills[pillIndex].classList.add('active');
  }

  // Sayfa başa dönsün
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === 'tab-library') {
    loadLibrary();
  }
}

function setDijitalMod(mod, btn) {
  activeDijitalMod = mod;
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function setWebMod(mod, btn) {
  activeWebMod = mod;
  btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ==============================================================================
// 1. DİJİTAL KİTAPLAR (Altın Karne / Sınav Dijital)
// ==============================================================================

const dijitalUrlInput = document.getElementById('dijital-url');
const dijitalAnalizBtn = document.getElementById('dijital-analiz-btn');
const dijitalSonuc = document.getElementById('dijital-sonuc');
const dijitalBatchSonuc = document.getElementById('dijital-batch-sonuc');
const dijitalIndirBtn = document.getElementById('dijital-indir-btn');
const dijitalBatchIndirBtn = document.getElementById('dijital-batch-indir-btn');
const dijitalProgress = document.getElementById('dijital-progress');

if (dijitalAnalizBtn) {
  dijitalAnalizBtn.addEventListener('click', async () => {
    const url = dijitalUrlInput.value.trim();
    if (!url) return alert('Lütfen bir link veya kitap ID giriniz.');

    dijitalAnalizBtn.disabled = true;
    dijitalAnalizBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İncele';
    dijitalSonuc.style.display = 'none';
    if (dijitalBatchSonuc) dijitalBatchSonuc.style.display = 'none';
    dijitalProgress.style.display = 'none';
    const actD = document.getElementById('dijital-tamam-actions');
    if (actD) { actD.style.display = 'none'; actD.innerHTML = ''; }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      if (json.is_batch && json.books && json.books.length > 0) {
        // Toplu Dijital Kitaplar
        activeDijitalBatchBooks = json.books;
        document.getElementById('dijital-batch-count').innerText = activeDijitalBatchBooks.length;
        const listEl = document.getElementById('dijital-batch-list');
        listEl.innerHTML = activeDijitalBatchBooks.map((b, i) => `
          <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:8px; padding:8px 10px; font-size:0.80rem; color:#FFF; display:flex; justify-content:space-between; align-items:center;">
            <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:8px;">
              <b>${i + 1}. ${b.title}</b> <span style="font-size:0.72rem; color:var(--text-sub);">(${b.platform_label || b.platform})</span>
            </div>
            <span style="background:rgba(16,185,129,0.2); color:#10B981; border:1px solid #10B981; font-size:0.70rem; padding:2px 6px; border-radius:4px; font-weight:700; flex-shrink:0;">
              ${b.pages_count} Sayfa
            </span>
          </div>
        `).join('');
        dijitalBatchSonuc.style.display = 'block';
      } else {
        // Tek Kitap
        activeDijitalData = json.data;
        document.getElementById('dijital-etiket').innerText = activeDijitalData.platform_label || 'Altın Karne';
        document.getElementById('dijital-baslik').innerText = activeDijitalData.title;
        document.getElementById('dijital-sayfa').innerText = activeDijitalData.pages_count;
        document.getElementById('dijital-cozum-durum').innerText = activeDijitalData.has_solution ? 'Var' : 'Yok';
        if (activeDijitalData.cover_url) {
          document.getElementById('dijital-kapak').src = activeDijitalData.cover_url;
        }
        dijitalSonuc.style.display = 'block';
      }
    } catch (err) {
      alert('Analiz Hatası: ' + err.message);
    } finally {
      dijitalAnalizBtn.disabled = false;
      dijitalAnalizBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> İncele & Analiz Et';
    }
  });
}

if (dijitalIndirBtn) {
  dijitalIndirBtn.addEventListener('click', async () => {
    if (!activeDijitalData) return;
    if (downloadingState.dijital) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.dijital = true;
    dijitalIndirBtn.disabled = true;
    if (dijitalAnalizBtn) dijitalAnalizBtn.disabled = true;
    dijitalIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    dijitalProgress.style.display = 'block';
    document.getElementById('dijital-prog-msg').innerText = 'İndirme başlatılıyor...';
    document.getElementById('dijital-prog-fill').style.width = '2%';
    document.getElementById('dijital-prog-pct').innerText = '%0';
    document.getElementById('dijital-prog-detail').innerText = '0 / ' + (activeDijitalData.pages_count || 0);
    document.getElementById('dijital-tamam-actions').style.display = 'none';
    dijitalProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('dijital-url');

    try {
      const res = await fetch('/api/start_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_data: activeDijitalData,
          mod: activeDijitalMod,
          quality: 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'dijital');
    } catch (err) {
      alert('İndirme Başlatılamadı: ' + err.message);
      downloadingState.dijital = false;
      dijitalIndirBtn.disabled = false;
      dijitalIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> PDF İNDİR (BAŞLAT)';
      if (dijitalAnalizBtn) dijitalAnalizBtn.disabled = false;
    }
  });
}

if (dijitalBatchIndirBtn) {
  dijitalBatchIndirBtn.addEventListener('click', async () => {
    if (!activeDijitalBatchBooks || activeDijitalBatchBooks.length === 0) return;
    if (downloadingState.dijital) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.dijital = true;
    dijitalBatchIndirBtn.disabled = true;
    if (dijitalAnalizBtn) dijitalAnalizBtn.disabled = true;
    dijitalBatchIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    dijitalProgress.style.display = 'block';
    document.getElementById('dijital-prog-msg').innerText = 'Toplu indirme başlatılıyor...';
    document.getElementById('dijital-prog-fill').style.width = '2%';
    document.getElementById('dijital-prog-pct').innerText = '%0';
    document.getElementById('dijital-prog-detail').innerText = '0 / ' + activeDijitalBatchBooks.length;
    document.getElementById('dijital-tamam-actions').style.display = 'none';
    dijitalProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('dijital-url');

    try {
      const res = await fetch('/api/start_batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          books: activeDijitalBatchBooks,
          mod: activeDijitalMod,
          quality: 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'dijital');
    } catch (err) {
      alert('Toplu İndirme Başlatılamadı: ' + err.message);
      downloadingState.dijital = false;
      dijitalBatchIndirBtn.disabled = false;
      dijitalBatchIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU DİJİTAL)';
      if (dijitalAnalizBtn) dijitalAnalizBtn.disabled = false;
    }
  });
}

// ==============================================================================
// 2. WEB Z-KİTAP MOTORU (Fernus & Fenomen - 141 Yayınevi)
// ==============================================================================

const webUrlInput = document.getElementById('web-url');
const webAnalizBtn = document.getElementById('web-analiz-btn');
const webSonuc = document.getElementById('web-sonuc');
const webBatchSonuc = document.getElementById('web-batch-sonuc');
const webIndirBtn = document.getElementById('web-indir-btn');
const webBatchIndirBtn = document.getElementById('web-batch-indir-btn');
const webProgress = document.getElementById('web-progress');

if (webAnalizBtn) {
  webAnalizBtn.addEventListener('click', async () => {
    const url = webUrlInput.value.trim();
    if (!url) return alert('Lütfen bir Fernus, Newton, İmpark veya Fenomen linki giriniz.');

    webAnalizBtn.disabled = true;
    webAnalizBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İncele';
    webSonuc.style.display = 'none';
    if (webBatchSonuc) webBatchSonuc.style.display = 'none';
    webProgress.style.display = 'none';
    const actW = document.getElementById('web-tamam-actions');
    if (actW) { actW.style.display = 'none'; actW.innerHTML = ''; }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      if (json.is_batch && json.books && json.books.length > 0) {
        // Toplu Kitaplar
        activeBatchBooks = json.books;
        document.getElementById('web-batch-count').innerText = activeBatchBooks.length;
        const listEl = document.getElementById('web-batch-list');
        listEl.innerHTML = activeBatchBooks.map((b, i) => `
          <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:8px; padding:8px 10px; font-size:0.80rem; color:#FFF; display:flex; justify-content:space-between; align-items:center;">
            <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:8px;">
              <b>${i + 1}. ${b.title}</b> <span style="font-size:0.72rem; color:var(--text-sub);">(${b.platform_label || b.platform})</span>
            </div>
            <span style="background:rgba(16,185,129,0.2); color:#10B981; border:1px solid #10B981; font-size:0.70rem; padding:2px 6px; border-radius:4px; font-weight:700; flex-shrink:0;">
              ${b.pages_count} Sayfa
            </span>
          </div>
        `).join('');
        webBatchSonuc.style.display = 'block';
      } else {
        // Tek Kitap
        activeWebData = json.data;
        document.getElementById('web-etiket').innerText = activeWebData.platform_label || 'Fernus Web';
        document.getElementById('web-baslik').innerText = activeWebData.title;
        webSonuc.style.display = 'block';
      }
    } catch (err) {
      alert('Analiz Hatası:\n' + err.message);
    } finally {
      webAnalizBtn.disabled = false;
      webAnalizBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> İncele & Analiz Et';
    }
  });
}

if (webIndirBtn) {
  webIndirBtn.addEventListener('click', async () => {
    if (!activeWebData) return;
    if (downloadingState.web) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.web = true;
    webIndirBtn.disabled = true;
    if (webAnalizBtn) webAnalizBtn.disabled = true;
    webIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    webProgress.style.display = 'block';
    document.getElementById('web-prog-msg').innerText = 'İndirme başlatılıyor...';
    document.getElementById('web-prog-fill').style.width = '2%';
    document.getElementById('web-prog-pct').innerText = '%0';
    document.getElementById('web-prog-detail').innerText = '0 / ' + (activeWebData.pages_count || 0);
    document.getElementById('web-tamam-actions').style.display = 'none';
    webProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('web-url');

    try {
      const res = await fetch('/api/start_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_data: activeWebData,
          mod: activeWebMod,
          quality: activeQuality || 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'web');
    } catch (err) {
      alert('İndirme Başlatılamadı: ' + err.message);
      downloadingState.web = false;
      webIndirBtn.disabled = false;
      webIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> PDF İNDİR (BAŞLAT)';
      if (webAnalizBtn) webAnalizBtn.disabled = false;
    }
  });
}

if (webBatchIndirBtn) {
  webBatchIndirBtn.addEventListener('click', async () => {
    if (!activeBatchBooks || activeBatchBooks.length === 0) return;
    if (downloadingState.web) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.web = true;
    webBatchIndirBtn.disabled = true;
    if (webAnalizBtn) webAnalizBtn.disabled = true;
    webBatchIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    webProgress.style.display = 'block';
    document.getElementById('web-prog-msg').innerText = 'Toplu indirme başlatılıyor...';
    document.getElementById('web-prog-fill').style.width = '2%';
    document.getElementById('web-prog-pct').innerText = '%0';
    document.getElementById('web-prog-detail').innerText = '0 / ' + activeBatchBooks.length;
    document.getElementById('web-tamam-actions').style.display = 'none';
    webProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('web-url');

    try {
      const res = await fetch('/api/start_batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          books: activeBatchBooks,
          mod: activeWebMod,
          quality: activeQuality || 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'web');
    } catch (err) {
      alert('Toplu İndirme Başlatılamadı: ' + err.message);
      downloadingState.web = false;
      webBatchIndirBtn.disabled = false;
      webBatchIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU PDF)';
      if (webAnalizBtn) webAnalizBtn.disabled = false;
    }
  });
}

// ==============================================================================
// 3. FLIP & SUPARA & FLIPHTML5
// ==============================================================================

const flipUrlInput = document.getElementById('flip-url');
const flipAnalizBtn = document.getElementById('flip-analiz-btn');
const flipSonuc = document.getElementById('flip-sonuc');
const flipBatchSonuc = document.getElementById('flip-batch-sonuc');
const flipIndirBtn = document.getElementById('flip-indir-btn');
const flipBatchIndirBtn = document.getElementById('flip-batch-indir-btn');
const flipProgress = document.getElementById('flip-progress');

if (flipAnalizBtn) {
  flipAnalizBtn.addEventListener('click', async () => {
    const url = flipUrlInput.value.trim();
    if (!url) return alert('Lütfen bir FlipHTML5, Newton veya Supara linki giriniz.');

    flipAnalizBtn.disabled = true;
    flipAnalizBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İncele';
    flipSonuc.style.display = 'none';
    if (flipBatchSonuc) flipBatchSonuc.style.display = 'none';
    flipProgress.style.display = 'none';
    const actF = document.getElementById('flip-tamam-actions');
    if (actF) { actF.style.display = 'none'; actF.innerHTML = ''; }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      if (json.is_batch && json.books && json.books.length > 0) {
        // Toplu Flip Kitapları
        activeFlipBatchBooks = json.books;
        document.getElementById('flip-batch-count').innerText = activeFlipBatchBooks.length;
        const listEl = document.getElementById('flip-batch-list');
        listEl.innerHTML = activeFlipBatchBooks.map((b, i) => `
          <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:8px; padding:8px 10px; font-size:0.80rem; color:#FFF; display:flex; justify-content:space-between; align-items:center;">
            <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:8px;">
              <b>${i + 1}. ${b.title}</b> <span style="font-size:0.72rem; color:var(--text-sub);">(${b.platform_label || b.platform})</span>
            </div>
            <span style="background:rgba(16,185,129,0.2); color:#10B981; border:1px solid #10B981; font-size:0.70rem; padding:2px 6px; border-radius:4px; font-weight:700; flex-shrink:0;">
              ${b.pages_count} Sayfa
            </span>
          </div>
        `).join('');
        flipBatchSonuc.style.display = 'block';
      } else {
        // Tek Kitap
        activeFlipData = json.data;
        document.getElementById('flip-baslik').innerText = activeFlipData.title;
        document.getElementById('flip-sayfa').innerText = activeFlipData.pages_count;
        document.getElementById('flip-etiket').innerText = activeFlipData.platform_label || 'Supara Jet';
        flipSonuc.style.display = 'block';
      }
    } catch (err) {
      alert('Analiz Hatası:\n' + err.message);
    } finally {
      flipAnalizBtn.disabled = false;
      flipAnalizBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> İncele & Analiz Et';
    }
  });
}

if (flipIndirBtn) {
  flipIndirBtn.addEventListener('click', async () => {
    if (!activeFlipData) return;
    if (downloadingState.flip) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.flip = true;
    flipIndirBtn.disabled = true;
    if (flipAnalizBtn) flipAnalizBtn.disabled = true;
    flipIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    flipProgress.style.display = 'block';
    document.getElementById('flip-prog-msg').innerText = 'İndirme başlatılıyor...';
    document.getElementById('flip-prog-fill').style.width = '2%';
    document.getElementById('flip-prog-pct').innerText = '%0';
    document.getElementById('flip-prog-detail').innerText = '0 / ' + (activeFlipData.pages_count || 0);
    document.getElementById('flip-tamam-actions').style.display = 'none';
    flipProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('flip-url');

    try {
      const res = await fetch('/api/start_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_data: activeFlipData,
          mod: 1,
          quality: activeQuality || 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'flip');
    } catch (err) {
      alert('İndirme Başlatılamadı: ' + err.message);
      downloadingState.flip = false;
      flipIndirBtn.disabled = false;
      flipIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> PDF İNDİR (JET MOTORU)';
      if (flipAnalizBtn) flipAnalizBtn.disabled = false;
    }
  });
}

if (flipBatchIndirBtn) {
  flipBatchIndirBtn.addEventListener('click', async () => {
    if (!activeFlipBatchBooks || activeFlipBatchBooks.length === 0) return;
    if (downloadingState.flip) {
      alert('Şu anda devam eden bir indirme işlemi var. Lütfen tamamlanmasını bekleyiniz.');
      return;
    }
    downloadingState.flip = true;
    flipBatchIndirBtn.disabled = true;
    if (flipAnalizBtn) flipAnalizBtn.disabled = true;
    flipBatchIndirBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';

    flipProgress.style.display = 'block';
    document.getElementById('flip-prog-msg').innerText = 'Toplu indirme başlatılıyor...';
    document.getElementById('flip-prog-fill').style.width = '2%';
    document.getElementById('flip-prog-pct').innerText = '%0';
    document.getElementById('flip-prog-detail').innerText = '0 / ' + activeFlipBatchBooks.length;
    document.getElementById('flip-tamam-actions').style.display = 'none';
    flipProgress.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    clearInputBox('flip-url');

    try {
      const res = await fetch('/api/start_batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          books: activeFlipBatchBooks,
          mod: 1,
          quality: activeQuality || 100
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);

      pollProgress(json.task_id, 'flip');
    } catch (err) {
      alert('Toplu İndirme Başlatılamadı: ' + err.message);
      downloadingState.flip = false;
      flipBatchIndirBtn.disabled = false;
      flipBatchIndirBtn.innerHTML = '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU FLIP)';
      if (flipAnalizBtn) flipAnalizBtn.disabled = false;
    }
  });
}

// ==============================================================================
// ORTAK İLERLEME TAKİBİ VE BUTONLAR
// ==============================================================================

function pollProgress(taskId, prefix) {
  const msgEl = document.getElementById(`${prefix}-prog-msg`);
  const fillEl = document.getElementById(`${prefix}-prog-fill`);
  const detailEl = document.getElementById(`${prefix}-prog-detail`);
  const pctEl = document.getElementById(`${prefix}-prog-pct`);
  const actionEl = document.getElementById(`${prefix}-tamam-actions`);
  const btnEl = document.getElementById(`${prefix}-indir-btn`);
  const batchBtnEl = document.getElementById(`${prefix}-batch-indir-btn`);
  const analizBtn = document.getElementById(`${prefix}-analiz-btn`);
  const progBox = document.getElementById(`${prefix}-progress`);

  if (progBox) progBox.style.display = 'block';

  const defaultBtnText = prefix === 'dijital' ? '<i class="fa-solid fa-download"></i> PDF İNDİR (BAŞLAT)'
    : prefix === 'web' ? '<i class="fa-solid fa-download"></i> PDF İNDİR (BAŞLAT)'
    : '<i class="fa-solid fa-download"></i> PDF İNDİR (JET MOTORU)';

  const defaultBatchBtnText = prefix === 'dijital' ? '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU DİJİTAL)'
    : prefix === 'web' ? '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU PDF)'
    : '<i class="fa-solid fa-download"></i> TÜMÜNÜ İNDİR (TOPLU FLIP)';

  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/progress?id=${taskId}`);
      const json = await res.json();
      if (!json.success) return;

      const task = json.task;
      if (msgEl) msgEl.innerText = task.message || 'İşleniyor...';
      if (fillEl) fillEl.style.width = `${task.progress}%`;
      if (pctEl) pctEl.innerText = `%${task.progress}`;
      if (detailEl) detailEl.innerText = `${task.completed || 0} / ${task.total || 0}`;

      if (task.status === 'completed') {
        clearInterval(interval);
        downloadingState[prefix] = false;
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.innerHTML = defaultBtnText;
        }
        if (batchBtnEl) {
          batchBtnEl.disabled = false;
          batchBtnEl.innerHTML = defaultBatchBtnText;
        }
        if (analizBtn) analizBtn.disabled = false;

        if (navigator.vibrate) navigator.vibrate([100, 50, 100]);

        // Kütüphane sayacını güncelle
        updateLibraryCount();

        const filesList = task.pdf_files_info || (task.pdf_files || []).map(f => ({ name: f, url: `/pdf/${encodeURIComponent(f)}`, short_url: '' }));

        // 1. PDF BİTTİĞİNDE TELEFONA OTOMATİK İNDİR
        // Tek kitap ise otomatik indir, çoklu kitapta ilkini indirip diğerlerini kartlardaki butonlarla sun (tarayıcı blokajını önler)
        if (filesList.length > 0) {
          downloadPdfDirect(filesList[0].name, filesList[0].url, null);
        }

        // Tamamlandı Kartları (Sade, temiz ve pratik)
        let html = '<div style="display:flex; flex-direction:column; gap:10px; margin-top:12px;">';
        if (filesList.length > 1) {
          html += `
            <div style="background:rgba(16, 185, 129, 0.15); border:1px solid #10B981; border-radius:10px; padding:10px; color:#34D399; font-size:0.86rem; text-align:center; font-weight:700;">
              🎉 Toplam ${filesList.length} Adet PDF Başarıyla Hazırlandı!
            </div>
          `;
        }

        filesList.forEach((item, idx) => {
          const safeName = item.name.replace(/'/g, "\\'");
          html += `
            <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:12px; padding:12px;">
              <div style="font-weight:700; font-size:0.88rem; margin-bottom:10px; color:#FFF; word-break:break-word;">
                📄 ${item.name}
              </div>
              <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
                <a href="${item.url}" download="${item.name}" class="btn" style="background:#F59E0B; color:#000; font-weight:700; padding:10px; font-size:0.82rem; text-decoration:none; display:flex; align-items:center; justify-content:center; gap:6px;">
                  <i class="fa-solid fa-download"></i> Telefona İndir
                </a>
                <button onclick="sharePdfToWhatsApp('${safeName}')" class="btn" style="background:#25D366; color:#FFF; padding:10px; font-size:0.82rem;">
                  <i class="fa-brands fa-whatsapp"></i> WhatsApp'a At
                </button>
              </div>
              <button onclick="copyAndShareLink('${safeName}', '${item.short_url}', '${item.url}')" class="btn btn-secondary" style="width:100%; padding:9px; font-size:0.80rem;">
                <i class="fa-solid fa-copy"></i> Paylaşım Linkini Kopyala
              </button>
            </div>
          `;
        });
        html += '</div>';
        if (actionEl) {
          actionEl.innerHTML = html;
          actionEl.style.display = 'block';
        }
      } else if (task.status === 'failed') {
        clearInterval(interval);
        downloadingState[prefix] = false;
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.innerHTML = defaultBtnText;
        }
        if (batchBtnEl) {
          batchBtnEl.disabled = false;
          batchBtnEl.innerHTML = defaultBatchBtnText;
        }
        if (analizBtn) analizBtn.disabled = false;
        alert('Hata Oluştu: ' + task.message);
      }
    } catch (e) {
      // Devam et
    }
  }, 800);
}

// 1. Doğrudan Telefona İndirme
function downloadPdfDirect(fileName, downloadUrl, btnElement) {
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  markFileDownloaded(fileName);
  if (btnElement) {
    btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Telefona İndirildi';
    btnElement.style.background = '#059669';
  }
}

// 2. WhatsApp ile Gerçek PDF Dosyası Gönderme Rehberi
function sharePdfToWhatsApp(fileName) {
  showWaModal(
    `<div style="text-align:center; padding:5px 0;">
       <i class="fa-brands fa-whatsapp" style="font-size:3.2rem; color:#25D366; margin-bottom:10px;"></i>
       <div style="font-size:1.05rem; font-weight:800; color:#FFF; margin-bottom:6px;">WhatsApp'a PDF Gönderme</div>
       <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:12px; padding:12px; font-size:0.84rem; color:#CBD5E1; text-align:left; line-height:1.6; margin-bottom:12px;">
         ✅ <b>"${fileName}"</b> telefonunuzun <b>İndirilenler (Downloads)</b> klasörüne indirildi.<br><br>
         WhatsApp açıldığında göndereceğiniz sohbette:<br>
         1️⃣ <b>Ataç (📎)</b> simgesine dokunun<br>
         2️⃣ <b>Belge (📄)</b> seçin<br>
         3️⃣ En üstteki <b>"${fileName}"</b> dosyasını seçip gönderin!
       </div>
     </div>`,
    () => {
      window.location.href = `https://api.whatsapp.com/send?text=${encodeURIComponent('📚 *' + fileName + '*')}`;
    },
    '<i class="fa-brands fa-whatsapp"></i> WhatsApp\'ı Aç',
    '#25D366'
  );
}

// 3. Linki Otomatik Kopyala & Paylaş (Telegram, Chrome, WhatsApp)
function copyAndShareLink(fileName, shortUrl, downloadUrl) {
  const targetPath = shortUrl || downloadUrl;
  const cleanLink = `${window.location.origin}${targetPath}`;

  // Otomatik olarak panoya kopyala
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(cleanLink).catch(() => {});
  } else {
    try {
      const ta = document.createElement('textarea');
      ta.value = cleanLink;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    } catch(e) {}
  }

  // Kullanıcıya şık ve net seçenek sun
  showWaModal(
    `<div style="text-align:center; padding:5px 0;">
       <i class="fa-solid fa-clipboard-check" style="font-size:3rem; color:#10B981; margin-bottom:10px;"></i>
       <div style="font-size:1.05rem; font-weight:800; color:#FFF; margin-bottom:6px;">Link Panoya Kopyalandı!</div>
       <div style="background:#0A122A; border:1px solid #1E2D5A; border-radius:10px; padding:10px; font-family:monospace; color:#FFD700; font-size:0.95rem; margin-bottom:12px; word-break:break-all;">
         ${cleanLink}
       </div>
       <p style="color:#CBD5E1; font-size:0.82rem; line-height:1.5;">Bağlantı panoya kopyalandı. Telegram, Chrome veya WhatsApp'a doğrudan yapıştırabilirsiniz.</p>
     </div>`,
    () => {
      const msg = `📚 *${fileName}*\n\n🔗 *İndirme Linki:*\n${cleanLink}`;
      window.location.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`;
    },
    '<i class="fa-brands fa-whatsapp"></i> WhatsApp\'ta Paylaş',
    '#25D366'
  );
}

// WhatsApp Bilgi Modal Fonksiyonları
function showWaModal(htmlContent, onConfirm, confirmBtnHtml = '<i class="fa-brands fa-whatsapp"></i> WhatsApp\'ı Aç', btnColor = '#25D366') {
  const modal = document.getElementById('wa-modal');
  const textEl = document.getElementById('wa-modal-text');
  const btnEl = document.getElementById('wa-modal-btn');
  textEl.innerHTML = htmlContent;
  btnEl.innerHTML = confirmBtnHtml;
  btnEl.style.background = btnColor;
  btnEl.onclick = () => {
    closeWaModal();
    if (onConfirm) onConfirm();
  };
  modal.style.display = 'flex';
}

function closeWaModal() {
  const modal = document.getElementById('wa-modal');
  if (modal) modal.style.display = 'none';
}

// ==============================================================================
// 4. KÜTÜPHANEM
// ==============================================================================

async function loadLibrary() {
  const libEl = document.getElementById('library-list');
  libEl.innerHTML = '<div style="text-align: center; color: var(--text-sub); padding: 25px;"><i class="fa-solid fa-spinner fa-spin"></i> Kitaplar Yükleniyor...</div>';
  try {
    const res = await fetch('/api/library');
    const json = await res.json();
    if (!json.success || !json.files.length) {
      libEl.innerHTML = '<div style="text-align: center; color: var(--text-sub); padding: 25px;">Henüz indirilmiş kitap yok.</div>';
      updateCountBadges(0);
      return;
    }

    updateCountBadges(json.files.length);

    let html = '';
    json.files.forEach(f => {
      const isDl = downloadedFiles.has(f.name);
      const dlStyle = isDl ? 'background: #059669; color: #FFF;' : 'background: #10B981; color: #FFF;';
      const dlIcon = isDl ? 'fa-check' : 'fa-download';
      const dlTitle = isDl ? 'Telefona İndirildi' : 'Telefona İndir';
      html += `
        <div class="lib-item">
          <div class="lib-info">
            <div class="lib-name" title="${f.name}">${f.name}</div>
            <div class="lib-meta">
              <span><i class="fa-solid fa-hard-drive"></i> ${f.size_mb}</span>
              <span><i class="fa-regular fa-clock"></i> ${f.date}</span>
            </div>
          </div>
          <div class="lib-actions">
            <button onclick="downloadPdfDirect('${f.name}', '${f.url}', this)" class="lib-btn" style="${dlStyle}" title="${dlTitle}">
              <i class="fa-solid ${dlIcon}"></i>
            </button>
            <button onclick="sharePdfToWhatsApp('${f.name}')" class="lib-btn lib-btn-wa" title="WhatsApp Dosya Gönder">
              <i class="fa-brands fa-whatsapp"></i>
            </button>
            <button onclick="copyAndShareLink('${f.name}', '${f.short_url || ''}', '${f.url}')" class="lib-btn" style="background:#1E2D5A; color:#FFF;" title="Linki Kopyala & Paylaş">
              <i class="fa-solid fa-copy"></i>
            </button>
            <button onclick="deletePdf('${f.name}')" class="lib-btn lib-btn-del" title="Sil">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </div>
      `;
    });
    libEl.innerHTML = html;
  } catch (err) {
    libEl.innerHTML = '<div style="text-align: center; color: var(--danger); padding: 25px;">Liste yüklenemedi.</div>';
  }
}

function updateCountBadges(count) {
  const topEl = document.getElementById('top-lib-count');
  const btmEl = document.getElementById('bottom-lib-count');
  if (topEl) topEl.innerText = count;
  if (btmEl) btmEl.innerText = count;
}

async function updateLibraryCount() {
  try {
    const res = await fetch('/api/library');
    const json = await res.json();
    if (json.success && json.files) {
      updateCountBadges(json.files.length);
    }
  } catch (e) {}
}

async function deletePdf(name) {
  if (!confirm(`"${name}" dosyasını silmek istediğinize emin misiniz?`)) return;
  try {
    const res = await fetch('/api/delete_pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const json = await res.json();
    if (json.success) {
      loadLibrary();
    } else {
      alert('Silinemedi: ' + json.message);
    }
  } catch (e) {
    alert('Hata: ' + e.message);
  }
}

// Sayfa ilk yüklendiğinde kütüphane sayacını al
updateLibraryCount();

// Geriye dönük uyumluluk takma adları
window.sharePdfDocument = function(name, url) { sharePdfToWhatsApp(name); };
window.shareDownloadLink = function(name, shortUrl, url) { copyAndShareLink(name, shortUrl, url); };
