document.addEventListener('DOMContentLoaded', () => {
  const API_BASE = 'https://pdf-chatbot-7hnb.onrender.com/upload'; // Single base URL (combined app)

  const uBtn = document.getElementById('uBtn');
  const aBtn = document.getElementById('aBtn');
  const sBtn = document.getElementById('sBtn');

  const uModal = document.getElementById('uModal');
  const aModal = document.getElementById('aModal');
  const uOk = document.getElementById('uOk');
  const aOk = document.getElementById('aOk');
  const uClose = document.getElementById('uClose');
  const aClose = document.getElementById('aClose');


  const pdfIn = document.getElementById('pdfIn');
  const dropZone = document.getElementById('dropZone');
  const fileListEl = document.getElementById('fileList');
  const uploadProgress = document.getElementById('uploadProgress');
  const uploadProgressBar = document.getElementById('uploadProgressBar');
  const uploadProgressText = document.getElementById('uploadProgressText');
  const analyzeProgress = document.getElementById('analyzeProgress');
  const analyzeProgressBar = document.getElementById('analyzeProgressBar');
  const analyzeProgressText = document.getElementById('analyzeProgressText');
  const resultsEl = document.getElementById('results');
  const personaIn = document.getElementById('persona');
  const taskIn = document.getElementById('task');
  const askForm = document.querySelector('form');
  const askInput = askForm?.querySelector('input[type="text"]');
  const themeSelect = document.getElementById('themeSelect');

  // Theme switching
  function applyTheme(theme) {
    try {
      const t = theme || 'legacy';
      document.documentElement.setAttribute('data-theme', t);
    } catch (_) {}
  }
  function initTheme() {
    try {
      const saved = localStorage.getItem('rw_theme');
      const theme = saved || 'legacy';
      applyTheme(theme);
      if (themeSelect) themeSelect.value = theme;
    } catch (_) { applyTheme('legacy'); }
  }
  initTheme();
  themeSelect?.addEventListener('change', (e) => {
    const val = e.target?.value || 'legacy';
    applyTheme(val);
    try { localStorage.setItem('rw_theme', val); } catch (_) {}
  });

  // Helpers
  function renderJSON(obj) {
    try { resultsEl.textContent = JSON.stringify(obj, null, 2); } catch { resultsEl.textContent = String(obj); }
  }
  function toast(message, type = 'success') {
    const d = document.createElement('div');
    d.textContent = message;
    d.style.position = 'fixed';
    d.style.bottom = '1rem';
    d.style.right = '1rem';
    d.style.zIndex = 9999;
    d.style.padding = '0.5rem 0.75rem';
    d.style.borderRadius = '0.375rem';
    d.style.color = '#fff';
    d.style.fontWeight = '800';
    d.style.background = type === 'error' ? '#dc2626' : '#16a34a';
    d.style.boxShadow = '0 8px 32px rgba(0,0,0,.25)';
    document.body.appendChild(d);
    setTimeout(() => { d.style.opacity = '0'; d.style.transition = 'opacity 400ms'; }, 2200);
    setTimeout(() => d.remove(), 2700);
  }

  // Thinking indicator in results panel
  function showThinking(message) {
    if (!resultsEl) return;
    resultsEl.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'thinking';
    const ring = document.createElement('span');
    ring.className = 'spinner-ring';
    const msg = document.createElement('span');
    msg.className = 'msg';
    msg.textContent = message || 'Working...';
    wrap.appendChild(ring);
    wrap.appendChild(msg);
    resultsEl.appendChild(wrap);
  }

  // Clipboard helpers
  async function copyTextToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        return !!ok;
      } catch (e) {
        console.warn('Clipboard API failed', e);
        return false;
      }
    }
  }
  function markButtonCopied(btn, fallbackLabel = 'Copy') {
    if (!btn) return;
    const prev = btn.textContent;
    btn.textContent = 'Copied';
    btn.classList.add('success');
    setTimeout(() => {
      btn.textContent = prev || fallbackLabel;
      btn.classList.remove('success');
    }, 1400);
  }

  // Upload progress helpers
  function setUploadProgress(pct) {
    if (!uploadProgress || !uploadProgressBar || !uploadProgressText) return;
    uploadProgress.classList.remove('hidden');
    const val = Math.max(0, Math.min(100, Math.round(pct)));
    uploadProgressBar.style.width = val + '%';
    uploadProgressText.textContent = val + '%';
  }
  function setUploadError() {
    if (!uploadProgress || !uploadProgressBar || !uploadProgressText) return;
    uploadProgress.classList.remove('hidden');
    uploadProgressBar.classList.add('error');
  }
  function setUploadLabel(text) {
    if (!uploadProgress) return;
    const label = uploadProgress.querySelector('.progress-label');
    if (label) label.childNodes[0].nodeValue = text + ' ';
  }

  // Analyze progress helpers
  function setAnalyzeProgress(pct) {
    if (!analyzeProgress || !analyzeProgressBar || !analyzeProgressText) return;
    analyzeProgress.classList.remove('hidden');
    const val = Math.max(0, Math.min(100, Math.round(pct)));
    analyzeProgressBar.style.width = val + '%';
    analyzeProgressText.textContent = val + '%';
  }
  function setAnalyzeLabel(text) {
    if (!analyzeProgress) return;
    const label = analyzeProgress.querySelector('.progress-label');
    if (label) label.childNodes[0].nodeValue = text + ' ';
  }
  function setAnalyzeError() {
    if (!analyzeProgress || !analyzeProgressBar) return;
    analyzeProgress.classList.remove('hidden');
    analyzeProgressBar.classList.add('error');
  }

  // Render selected file names into the list
  function renderFileList() {
    if (!fileListEl || !pdfIn) return;
    try {
      fileListEl.innerHTML = '';
      const files = pdfIn.files ? Array.from(pdfIn.files) : [];
      if (!files.length) return;
      files.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.name;
        fileListEl.appendChild(li);
      });
    } catch (_) {}
  }

  // Setup drag & drop on the drop zone
  if (dropZone && pdfIn) {
    const prevent = e => { e.preventDefault(); e.stopPropagation(); };
    ['dragenter', 'dragover'].forEach(evt => {
      dropZone.addEventListener(evt, e => {
        prevent(e);
        try { e.dataTransfer.dropEffect = 'copy'; } catch(_) {}
        dropZone.classList.add('is-dragover');
      });
    });
    ;['dragleave', 'dragend'].forEach(evt => {
      dropZone.addEventListener(evt, e => {
        prevent(e);
        dropZone.classList.remove('is-dragover');
      });
    });
    dropZone.addEventListener('drop', e => {
      prevent(e);
      dropZone.classList.remove('is-dragover');
      const incoming = Array.from(e.dataTransfer?.files || []);
      const pdfs = incoming.filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'));
      if (!pdfs.length) {
        try { toast('Only PDF files are supported.', 'error'); } catch(_) {}
        return;
      }
      try {
        const dt = new DataTransfer();
        const existing = pdfIn.files ? Array.from(pdfIn.files) : [];
        const seen = new Set();
        // keep existing
        existing.forEach(f => {
          const key = `${f.name}|${f.size}`;
          if (!seen.has(key)) { seen.add(key); dt.items.add(f); }
        });
        // add new
        pdfs.forEach(f => {
          const key = `${f.name}|${f.size}`;
          if (!seen.has(key)) { seen.add(key); dt.items.add(f); }
        });
        pdfIn.files = dt.files;
        renderFileList();
        try { toast(`Added ${pdfs.length} file(s)`); } catch(_) {}
      } catch (err) {
        console.warn('Drop failed', err);
      }
    });
    // Click to open file chooser
    dropZone.addEventListener('click', () => { try { pdfIn.click(); } catch(_) {} });
    // Sync list when choosing with file input
    pdfIn.addEventListener('change', renderFileList);
  }

  // Mark frontend ready for quick visual check
  try {
    console.log('[UI] Frontend ready');
    if (resultsEl) resultsEl.textContent = 'Ready';
  } catch(_) {}

  // Pretty renderer for Analyze results
  function displayAnalysisResult(result) {
    // Clear and render structured analysis
    resultsEl.innerHTML = '';
    const container = document.createElement('div');
    container.id = 'analysis-output';
    const card = document.createElement('div');
    card.classList.add('summary-card');

    const subsectionAnalysis = Array.isArray(result?.subsection_analysis) ? result.subsection_analysis : [];
    const extractedSections = Array.isArray(result?.extracted_sections) ? result.extracted_sections : [];

    // Title for Subsection Analysis
    const header = document.createElement('div');
    header.classList.add('card-header');
    const title = document.createElement('h2');
    title.textContent = '🧠 Subsection Analysis';
    title.style.fontWeight = '800';
    title.classList.add('gradient-text');
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    header.appendChild(title);
    header.appendChild(copyBtn);
    card.appendChild(header);
    const body = document.createElement('div');
    body.className = 'card-content';

    const filteredSubsections = subsectionAnalysis.filter(
      entry => entry?.refined_text && String(entry.refined_text).trim().length > 0
    );
    if (filteredSubsections.length) {
      const list = document.createElement('ul');
      list.style.listStyleType = 'disc';
      list.style.listStylePosition = 'outside';
      list.style.paddingLeft = '1.25rem';
      filteredSubsections.slice(0, 10).forEach(entry => {
        const li = document.createElement('li');
        const refined = String(entry.refined_text || '').trim();
        const score = (typeof entry.score === 'number') ? ` (score: ${entry.score.toFixed(3)})` : '';

        // Try to detect structured sub-points in refined text
        const bulletParts = refined.includes('•') ? refined.split(/•/).map(s => s.trim()).filter(Boolean)
                           : refined.split(/\r?\n/).map(s => s.replace(/^[-*–]\s*/, '').trim()).filter(Boolean);

        if (bulletParts.length > 1) {
          // Heading label for the parent item (first line), rest as nested bullets
          const head = bulletParts.shift();
          const headSpan = document.createElement('span');
          headSpan.classList.add('gradient-text');
          headSpan.textContent = head + score;
          li.appendChild(headSpan);

          const ul = document.createElement('ul');
          ul.style.listStyleType = 'circle';
          ul.style.listStylePosition = 'outside';
          ul.style.paddingLeft = '1.25rem';
          bulletParts.forEach(pt => {
            const li2 = document.createElement('li');
            const span2 = document.createElement('span');
            span2.classList.add('gradient-text');
            span2.textContent = pt;
            li2.appendChild(span2);
            ul.appendChild(li2);
          });
          li.appendChild(ul);
        } else {
          const span = document.createElement('span');
          span.classList.add('gradient-text');
          span.textContent = refined + score;
          li.appendChild(span);
        }
        list.appendChild(li);
      });
      body.appendChild(list);
    } else {
      const p = document.createElement('p');
      p.textContent = 'No subsection insights available.';
      p.classList.add('gradient-text');
      body.appendChild(p);
    }

    // Divider
    const hr = document.createElement('hr');
    hr.style.margin = '0.75rem 0';
    body.appendChild(hr);

    // Title for Extracted Sections
    const title2 = document.createElement('h3');
    title2.textContent = '📌 Top Extracted Sections';
    title2.style.fontWeight = '800';
    title2.style.marginBottom = '0.5rem';
    title2.classList.add('gradient-text');
    body.appendChild(title2);

    if (extractedSections.length) {
      const list2 = document.createElement('ol');
      list2.style.listStyleType = 'decimal';
      list2.style.listStylePosition = 'outside';
      list2.style.paddingLeft = '1.25rem';
      extractedSections.slice(0, 10).forEach(sec => {
        const li = document.createElement('li');
        const doc = sec?.document_title || sec?.document || '';
        const title = sec?.section_title || sec?.title || '';
        const span = document.createElement('span');
        span.classList.add('gradient-text');
        span.textContent = [doc, title].filter(Boolean).join(' — ');
        li.appendChild(span);
        list2.appendChild(li);
      });
      body.appendChild(list2);
    } else {
      const p2 = document.createElement('p');
      p2.textContent = 'No extracted sections available.';
      p2.classList.add('gradient-text');
      body.appendChild(p2);
    }

    // Wire copy button for the whole analysis card
    try {
      copyBtn.addEventListener('click', async () => {
        const text = `${title.textContent}\n\n${body.innerText}`.trim();
        const ok = await copyTextToClipboard(text);
        if (ok) markButtonCopied(copyBtn); else try { toast('Copy failed', 'error'); } catch(_) {}
      });
    } catch(_) {}

    card.appendChild(body);
    container.appendChild(card);
    resultsEl.appendChild(container);
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 50);
  }

  // Pretty renderer for Summary results (based on backend/output/summary.json structure)
  function displaySummaryResult(result) {
    resultsEl.innerHTML = '';
    const container = document.createElement('div');
    container.id = 'summary-output';

    const title = document.createElement('h3');
    title.textContent = '📝 Quick Summary';
    title.style.fontWeight = '800';
    title.style.marginBottom = '0.5rem';
    container.appendChild(title);

    // Grid container for per-document cards
    const grid = document.createElement('div');
    grid.classList.add('summary-grid');

    const items = Array.isArray(result) ? result : (Array.isArray(result?.data) ? result.data : []);
    if (!items.length) {
      const p = document.createElement('p');
      p.textContent = 'No summary available.';
      container.appendChild(p);
      resultsEl.appendChild(container);
      return; // Avoid appending container again
    }

    items.forEach(doc => {
      const docWrap = document.createElement('div');
      docWrap.classList.add('summary-card');
      // header with copy
      const header = document.createElement('div');
      header.className = 'card-header';
      const h4 = document.createElement('h4');
      h4.textContent = doc?.title || doc?.pdf_name || 'Untitled Document';
      h4.classList.add('gradient-text');
      h4.style.fontWeight = '700';
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.textContent = 'Copy';
      header.appendChild(h4);
      header.appendChild(copyBtn);
      docWrap.appendChild(header);
      // body content container
      const body = document.createElement('div');
      body.className = 'card-content';
    
      const headings = Array.isArray(doc?.headings) ? doc.headings : [];
      if (headings.length) {
        const list = document.createElement('ul');
        list.style.listStyle = 'disc';
        list.style.paddingLeft = '1.25rem';
        headings.slice(0, 10).forEach(h => {
          const li = document.createElement('li');
          const head = (h?.heading || '').trim();
          const sum = (h?.summary || '').trim();
    

          // If the summary contains bullet markers (•), render them as a nested list
          const parts = sum.split(/•/).map(s => s.trim()).filter(Boolean);
          if (parts.length > 1) {
            // Heading label
            const strong = document.createElement('strong');
            strong.textContent = head || 'Section';
            strong.classList.add('gradient-text'); // ensure label uses gradient too
            li.appendChild(strong);
            // Nested bullets
            const ul = document.createElement('ul');
            ul.style.listStyle = 'circle';
            ul.style.paddingLeft = '1.25rem';
            parts.forEach(b => {
              const li2 = document.createElement('li');
              // Wrap text in a gradient span to keep bullet marker visible
              const span = document.createElement('span');
              span.classList.add('gradient-text');
              span.textContent = b;
              li2.appendChild(span);
              ul.appendChild(li2);
            });
            li.appendChild(ul);
          } else {
            // Wrap the combined text in a gradient span so the bullet remains visible
            const span = document.createElement('span');
            span.classList.add('gradient-text');
            span.textContent = [head, sum].filter(Boolean).join(' — ');
            li.appendChild(span);
          }
          list.appendChild(li);
        });
        body.appendChild(list);
      } else {
        const p = document.createElement('p');
        p.textContent = 'No section summaries.';
        p.classList.add('gradient-text'); // ensure fallback text is gradient
        body.appendChild(p);
      }
      // wire copy for this document card
      try {
        copyBtn.addEventListener('click', async () => {
          const text = `${h4.textContent}\n\n${body.innerText}`.trim();
          const ok = await copyTextToClipboard(text);
          if (ok) markButtonCopied(copyBtn); else try { toast('Copy failed', 'error'); } catch(_) {}
        });
      } catch(_) {}

      docWrap.appendChild(body);
      grid.appendChild(docWrap);
    });

    // Append the grid of cards to the panel container, then render the panel
    container.appendChild(grid);
    resultsEl.appendChild(container);
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 50);

  }

  // Pretty renderer for Explain results (based on backend/output/explain_*.json structure)
  function displayExplainResult(result) {
    resultsEl.innerHTML = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const container = document.createElement('div');
    container.id = 'explain-output';
    const card = document.createElement('div');
    card.classList.add('summary-card');

    const header = document.createElement('div');
    header.className = 'card-header';
    const heading = document.createElement('h3');
    heading.textContent = '💡 Explanations';
    heading.style.fontWeight = '800';
    heading.classList.add('gradient-text');
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    header.appendChild(heading);
    header.appendChild(copyBtn);
    card.appendChild(header);
    const body = document.createElement('div');
    body.className = 'card-content';

    const items = Array.isArray(result) ? result : (Array.isArray(result?.data) ? result.data : []);
    if (!items.length) {
      const p = document.createElement('p');
      p.textContent = 'No explanation available.';
      p.classList.add('gradient-text');
      body.appendChild(p);
      card.appendChild(body);
      container.appendChild(card);
      resultsEl.appendChild(container);
      return;
    }

    // Show first 10 explanations
    const list = document.createElement('ol');
    list.style.listStyle = 'decimal';
    list.style.paddingLeft = '1.25rem';
    items.slice(0, 10).forEach(item => {
      const li = document.createElement('li');
      const title = item?.title || item?.pdf_name || 'Untitled Document';
      const para = document.createElement('div');
      para.style.marginTop = '0.25rem';
      para.textContent = (item?.explanation || '').trim();

      const strong = document.createElement('strong');
      strong.textContent = title;
      strong.classList.add('gradient-text');
      para.classList.add('gradient-text');
      li.appendChild(strong);
      li.appendChild(para);
      list.appendChild(li);
    });
    body.appendChild(list);

    // wire copy for whole explanations card
    try {
      copyBtn.addEventListener('click', async () => {
        const text = `${heading.textContent}\n\n${body.innerText}`.trim();
        const ok = await copyTextToClipboard(text);
        if (ok) markButtonCopied(copyBtn); else try { toast('Copy failed', 'error'); } catch(_) {}
      });
    } catch(_) {}

    card.appendChild(body);
    container.appendChild(card);
    resultsEl.appendChild(container);
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 50);
  }

  const hideModals = () => {
    try { uModal?.classList.add('hidden'); } catch(_) {}
    try { aModal?.classList.add('hidden'); } catch(_) {}
  };
  const showModal = (m) => {
    try { hideModals(); } catch(_) {}
    if (m && m.classList) {
      m.classList.remove('hidden');
    }
  };

  uBtn?.addEventListener('click', () => showModal(uModal));
  aBtn?.addEventListener('click', () => showModal(aModal));
  sBtn?.addEventListener('click', async () => {
    hideModals();
    try {
      showThinking('Summarizing your PDFs…');
      const resp = await fetch(`${API_BASE}/summary/`);
      if (!resp.ok) throw new Error(`Summary failed ${resp.status}`);
      console.debug('[HTTP] /summary status', resp.status);
      const data = await resp.json();
      console.debug('[HTTP] /summary JSON keys', Object.keys(data || {}));
      const payload = data?.data ?? data;
      // Render structured summary
      resultsEl.innerHTML = '';
      try { displaySummaryResult(payload); } catch (err) { console.warn('[WARN] displaySummaryResult failed', err); resultsEl.textContent = 'Error displaying summary.'; }
    } catch (e) {
      console.error('[ERR] summary', e);
      resultsEl.textContent = `Error (summary): ${e?.message || e}`;
    }
  });

  // Close/hide modals without surfacing any dock UI
  const minU = () => { uModal?.classList.add('hidden'); };
  const minA = () => { aModal?.classList.add('hidden'); };

  async function uploadAndRun() {
    try {
      const files = pdfIn?.files || [];
      if (!files.length) {
        alert('Please select one or more PDF files.');
        return;
      }
      // Prepare form data
      const formData = new FormData();
      for (const f of files) formData.append('files', f);

      // UI: disable button and show status
      const prevLabel = uOk.textContent;
      uOk.disabled = true;
      uOk.textContent = 'Uploading...';
      resultsEl.textContent = 'Uploading and processing...';

      // Use XHR to capture upload progress
      if (uploadProgressBar) uploadProgressBar.classList.remove('error');
      setUploadLabel('Uploading…');
      setUploadProgress(0);
      let displayPct = 0;
      let creepTimer = null;
      const data = await new Promise((resolve, reject) => {
        try {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', `${API_BASE}/stage1/upload/`);
          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              // Drive upload portion up to 80%
              const pct = Math.min(80, Math.max(2, (e.loaded / e.total) * 80));
              displayPct = pct;
              setUploadProgress(pct);
            }
          });
          xhr.upload.addEventListener('load', () => {
            // Upload finished; hold ~80% while backend processes
            displayPct = Math.max(displayPct, 80);
            setUploadProgress(displayPct);
            setUploadLabel('Processing…');
            if (!creepTimer) {
              creepTimer = setInterval(() => {
                displayPct = Math.min(95, displayPct + 1);
                setUploadProgress(displayPct);
              }, 400);
            }
          });
          xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
              if (xhr.status >= 200 && xhr.status < 300) {
                try {
                  const json = JSON.parse(xhr.responseText || 'null');
                  if (creepTimer) { clearInterval(creepTimer); creepTimer = null; }
                  // Mark 100% on completion
                  setUploadProgress(100);
                  setUploadLabel('Complete');
                  resolve(json);
                } catch (err) {
                  if (creepTimer) { clearInterval(creepTimer); creepTimer = null; }
                  reject(new Error('Invalid JSON response from backend.'));
                }
              } else {
                if (creepTimer) { clearInterval(creepTimer); creepTimer = null; }
                reject(new Error(`Backend error ${xhr.status}: ${xhr.responseText}`));
              }
            }
          };
          xhr.onerror = () => { if (creepTimer) { clearInterval(creepTimer); creepTimer = null; } reject(new Error('Network error')); };
          xhr.send(formData);
        } catch (err) {
          reject(err);
        }
      });
      console.log("Stage1 response:", data);
      
      // Store the document names for later steps
      try {
        let docs = [];
        if (Array.isArray(data)) {
          docs = data.map(o => o?.filename || o?.document).filter(Boolean);
        } else if (pdfIn?.files?.length) {
          docs = Array.from(pdfIn.files).map(f => f.name);
        }
        window.lastDocs = docs;
        if (docs.length) {
          localStorage.setItem('lastDocs', JSON.stringify(docs));
        }
      } catch(_) {}
      
      resultsEl.textContent = "✅ You are all set to ask questions!";
      resultsEl.style.color = "white"
      // Keep last Stage 1 outputs for Analyze step
      window.lastStage1 = data;
      // Also persist just the filenames to survive shape differences
      try {
        let docs = [];
        if (Array.isArray(data)) {
          docs = data.map(o => o?.filename || o?.document).filter(Boolean);
        } else if (pdfIn?.files?.length) {
          docs = Array.from(pdfIn.files).map(f => f.name);
        }
        window.lastDocs = docs;
        // Persist to localStorage so it survives refresh or modal toggles
        if (docs.length) {
          localStorage.setItem('lastDocs', JSON.stringify(docs));
        }
        console.debug('Stage1 documents captured:', docs);
      } catch(_) {}

      // Notify success
      try {
        const uploadedCount = Array.isArray(window.lastDocs) ? window.lastDocs.length : 0;
      } catch(_) {}

      // Minimize after success
      minU();
      // Auto-hide progress UI after a short delay
      try { setUploadProgress(100); } catch(_) {}
      setTimeout(() => { try { uploadProgress?.classList.add('hidden'); } catch(_) {} }, 1500);
      // restore label
      uOk.textContent = prevLabel || 'Done';
      uOk.disabled = false;
    } catch (err) {
      console.error(err);
      resultsEl.textContent = `Error: ${err?.message || err}`;
      setUploadError();
      uOk.textContent = 'Done';
      uOk.disabled = false;
    }
  }

  async function runAnalyze() {
    let aCreepTimer = null;
    try {
      const persona = personaIn?.value?.trim();
      const task = taskIn?.value?.trim();
      if (!persona || !task) {
        alert('Please enter both Persona and Task.');
        return;
      }
      // derive documents from lastStage1 (list from Stage 1 upload)
      // Prefer the persisted filenames from upload; fall back to lastStage1 or current file input
      let names = Array.isArray(window.lastDocs) ? window.lastDocs : [];
      if (!names.length) {
        try {
          const stored = localStorage.getItem('lastDocs');
          if (stored) names = JSON.parse(stored);
        } catch(_) {}
      }
      if (!names.length && Array.isArray(window.lastStage1)) {
        names = window.lastStage1.map(o => o?.filename || o?.document).filter(Boolean);
      }
      if (!names.length && pdfIn?.files?.length) {
        names = Array.from(pdfIn.files).map(f => f.name);
      }
      if (!names.length && resultsEl?.textContent) {
        // As a last resort, try to parse the visible results JSON
        try {
          const maybe = JSON.parse(resultsEl.textContent);
          if (Array.isArray(maybe)) {
            names = maybe.map(o => o?.filename || o?.document).filter(Boolean);
          } else if (maybe && Array.isArray(maybe.data)) {
            names = maybe.data.map(o => o?.filename || o?.document).filter(Boolean);
          }
        } catch(_) {}
      }
      console.debug('Analyze resolving document names:', names);
      if (!names.length) {
        console.warn('No document names resolved on frontend; proceeding to rely on backend auto-discovery.');
      }
      // Match script.js format (lines 272-342): include challenge_info and title
      const documents = names.map(name => ({ filename: name, title: name.replace(/\.[^.]+$/, '') }));
      const config = {
        challenge_info: {
          challenge_id: 'round_1b_002',
          test_case_name: 'custom_case',
          description: 'User Provided'
        },
        documents,
        persona: { role: persona },
        job_to_be_done: { task }
      };
      const blob = new Blob([JSON.stringify(config)], { type: 'application/json' });
      const fd = new FormData();
      fd.append('config', blob, 'challenge1b_input.json');

      const prev = aOk.textContent;
      aOk.disabled = true;
      aOk.textContent = 'Analyzing...';
      showThinking('Analyzing your collection…');

      // Init analyze progress bar
      if (analyzeProgressBar) analyzeProgressBar.classList.remove('error');
      setAnalyzeLabel('Processing…');
      setAnalyzeProgress(0);
      let aDisplayPct = 0;
      aCreepTimer = setInterval(() => {
        aDisplayPct = Math.min(95, aDisplayPct + 1);
        setAnalyzeProgress(aDisplayPct);
      }, 400);

      const resp = await fetch(`${API_BASE}/analyze/`, { method: 'POST', body: fd });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`Analyze failed ${resp.status}: ${txt}`);
      }
      console.debug('[HTTP] /analyze status', resp.status);
      const data = await resp.json();
      console.debug('[HTTP] /analyze JSON keys', Object.keys(data || {}));
      const payload = data?.data ?? data; // unwrap {status,data}
      // Always write raw JSON immediately so user sees something
      // First clear results
      resultsEl.innerHTML = "";
      // Render structured view only
      try { displayAnalysisResult(payload); } catch(err) {
        console.warn('[WARN] displayAnalysisResult failed', err);
        resultsEl.textContent = "Error displaying analysis result.";
      }

      // Success: mark 100% and hide shortly after
      if (aCreepTimer) { clearInterval(aCreepTimer); aCreepTimer = null; }
      try { setAnalyzeProgress(100); setAnalyzeLabel('Complete'); } catch(_) {}
      setTimeout(() => { try { analyzeProgress?.classList.add('hidden'); } catch(_) {} }, 1500);
      minA();
      aOk.textContent = prev || 'Start Analysis';
      aOk.disabled = false;
    } catch (e) {
      console.error('[ERR] analyze', e);
      resultsEl.textContent = `Error (analyze): ${e?.message || e}`;
      if (aCreepTimer) { clearInterval(aCreepTimer); aCreepTimer = null; }
      setAnalyzeError();
      aOk.textContent = 'Start Analysis';
      aOk.disabled = false;
    }
  }

  async function runExplain(ev) {
    ev?.preventDefault();
    const q = askInput?.value?.trim();
    if (!q) return;
    try {
      showThinking('Thinking…');
      const resp = await fetch(`${API_BASE}/explain/?topic=${encodeURIComponent(q)}`);
      if (!resp.ok) throw new Error(`Explain failed ${resp.status}`);
      console.debug('[HTTP] /explain status', resp.status);
      const data = await resp.json();
      console.debug('[HTTP] /explain JSON keys', Object.keys(data || {}));
      const payload = data?.data ?? data;
      resultsEl.innerHTML = '';
      try { displayExplainResult(payload); } catch (err) { console.warn('[WARN] displayExplainResult failed', err); resultsEl.textContent = 'Error displaying explanation.'; }
    } catch (e) {
      console.error('[ERR] explain', e);
      resultsEl.textContent = `Error (explain): ${e?.message || e}`;
    }
  }

  uOk?.addEventListener('click', uploadAndRun);
  uClose?.addEventListener('click', minU);
  aOk?.addEventListener('click', runAnalyze);
  aClose?.addEventListener('click', minA);

  askForm?.addEventListener('submit', runExplain);
  // Dock buttons removed
});
