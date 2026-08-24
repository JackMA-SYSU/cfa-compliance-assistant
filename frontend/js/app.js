/* 主逻辑 */
(function () {
  'use strict';

  const els = {
    netbar: document.getElementById('netbar'),
    nettext: document.getElementById('nettext'),
    behavior: document.getElementById('behavior'),
    voiceBtn: document.getElementById('voice-btn'),
    quickTags: document.getElementById('quick-tags'),
    analyzeBtn: document.getElementById('analyze-btn'),
    resultArea: document.getElementById('result-area'),
    stdSearch: document.getElementById('std-search'),
    standardsList: document.getElementById('standards-list'),
    historyList: document.getElementById('history-list'),
    exportBtn: document.getElementById('export-btn'),
    clearBtn: document.getElementById('clear-history-btn'),
    tabs: document.querySelectorAll('.tab'),
    views: document.querySelectorAll('.view'),
  };

  let currentResult = null;

  /* ---------- 视图切换 ---------- */
  els.tabs.forEach(tab => {
    tab.addEventListener('click', () => switchView(tab.dataset.view));
  });
  function switchView(name) {
    els.views.forEach(v => v.classList.toggle('active', v.id === `view-${name}`));
    els.tabs.forEach(t => {
      const active = t.dataset.view === name;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active);
    });
    if (name === 'standards') renderStandards(els.stdSearch.value);
    if (name === 'history') renderHistory();
  }

  /* ---------- 网络状态 ---------- */
  function updateNetState() {
    const online = navigator.onLine;
    els.netbar.classList.toggle('online', online);
    els.netbar.classList.toggle('offline', !online);
    els.netbar.classList.add('show');
    els.nettext.textContent = online ? '在线' : '离线（本地规则引擎）';
    if (online) flushPendingQueue();
  }
  window.addEventListener('online', updateNetState);
  window.addEventListener('offline', updateNetState);

  /* ---------- 快捷标签 ---------- */
  els.quickTags.addEventListener('click', (e) => {
    const btn = e.target.closest('.tag');
    if (btn) els.behavior.value = btn.dataset.text;
  });

  /* ---------- 语音输入 ---------- */
  els.voiceBtn.addEventListener('click', () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('当前浏览器不支持语音输入'); return; }
    const rec = new SR();
    rec.lang = 'zh-CN';
    rec.onresult = (e) => { els.behavior.value = e.results[0][0].transcript; };
    rec.start();
  });

  /* ---------- 分析流程 ---------- */
  els.analyzeBtn.addEventListener('click', doAnalyze);
  async function doAnalyze() {
    const text = els.behavior.value.trim();
    if (!text) { els.behavior.focus(); return; }

    els.analyzeBtn.disabled = true;
    els.analyzeBtn.textContent = '';
    els.analyzeBtn.innerHTML = '<div class="spinner"></div>';
    renderSkeleton();

    let result;
    if (API.getBaseUrl() && navigator.onLine) {
      try {
        result = await API.analyze(text);
      } catch (err) {
        // 后端不可达时回退本地
        result = offlineAnalyze(text);
        result.network_error = err.message;
      }
    } else {
      result = offlineAnalyze(text);
    }

    currentResult = result;
    renderResult(result);
    els.analyzeBtn.disabled = false;
    els.analyzeBtn.textContent = '开始合规自检';
  }

  function renderSkeleton() {
    els.resultArea.innerHTML = `
      <div class="skeleton" style="height:120px"></div>
      <div class="skeleton" style="height:80px"></div>
      <div class="skeleton" style="height:80px"></div>`;
  }

  /* ---------- 结果渲染 ---------- */
  function renderResult(r) {
    const risk = r.risk_level || 'mid';
    const standardsHtml = (r.standards || []).map(s => `
      <div class="std-item">
        <span class="std-code">${esc(s.code)}</span><span class="std-name">${esc(s.name)}</span>
        <div class="std-desc">${esc(s.description)}</div>
      </div>`).join('');

    const checklistHtml = (r.checklist || []).map((c, i) => `
      <li data-idx="${i}" class="${c.done ? 'done' : ''}" role="checkbox" aria-checked="${!!c.done}" tabindex="0">
        <span class="checkbox">${c.done ? '✓' : ''}</span>
        <span class="check-text">${esc(c.text)}</span>
      </li>`).join('');

    const casesHtml = (r.referenced_cases || []).map(c => `
      <div class="case-item">
        <span class="case-id">${esc(c.question_id)}</span>
        <span class="case-meta">相似度 ${(c.similarity * 100).toFixed(0)}% · 风险 ${esc(c.risk_level)}</span>
        <div class="case-summary">${esc((c.summary || '').slice(0, 100))}</div>
      </div>`).join('');

    els.resultArea.innerHTML = `
      <div class="risk-card ${risk}">
        <div class="risk-head">
          <span class="risk-level">${riskText(risk)}</span>
          <span class="risk-score">风险评分 ${r.risk_score ?? '—'}</span>
        </div>
        ${r.category && r.category !== 'uncertain' ? `<div class="case-meta">行为类别：${esc(categoryName(r.category))} · 置信度 ${Math.round((r.confidence || 0) * 100)}%</div>` : ''}
        ${r.risk_reasoning ? `<div class="risk-reason">${esc(r.risk_reasoning)}</div>` : ''}
      </div>
      ${r.network_error ? `<div class="advice" style="border-left:4px solid var(--warning)">⚠️ 后端不可用（${esc(r.network_error)}），已切换本地规则引擎</div>` : ''}
      <div class="section-title">涉及准则</div>
      ${standardsHtml || '<div class="empty">未明确命中具体准则</div>'}
      <div class="section-title">合规检查清单</div>
      <ul class="checklist">${checklistHtml || '<div class="empty">无需特别动作</div>'}</ul>
      ${r.action_advice ? `<div class="section-title">操作建议</div><div class="advice">${esc(r.action_advice)}</div>` : ''}
      ${r.disclosure_draft ? `<div class="section-title">披露草稿</div><div class="disclosure">${esc(r.disclosure_draft)}<br><button class="copy-btn">复制披露草稿</button></div>` : ''}
      ${casesHtml ? `<div class="section-title">类似题库案例</div>${casesHtml}` : ''}
    `;

    // 清单勾选交互
    els.resultArea.querySelectorAll('.checklist li').forEach(li => {
      li.addEventListener('click', () => toggleChecklistItem(li));
    });
    const copyBtn = els.resultArea.querySelector('.copy-btn');
    if (copyBtn) copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(r.disclosure_draft).then(() => copyBtn.textContent = '已复制 ✓');
    });

    // 保存到历史
    saveToHistory(r);
  }

  function toggleChecklistItem(li) {
    const idx = parseInt(li.dataset.idx, 10);
    const done = !li.classList.contains('done');
    li.classList.toggle('done', done);
    li.setAttribute('aria-checked', done);
    li.querySelector('.checkbox').textContent = done ? '✓' : '';
    if (currentResult && currentResult.checklist[idx]) {
      currentResult.checklist[idx].done = done;
      updateHistoryChecklist(idx, done);
    }
  }

  /* ---------- 历史记录 ---------- */
  async function saveToHistory(r) {
    const item = {
      id: Date.now(),
      behavior: els.behavior.value.trim(),
      result: r,
      created_at: new Date().toISOString(),
    };
    await Storage.saveSubmission(item);
  }

  async function updateHistoryChecklist(idx, done) {
    const items = await Storage.getSubmissions();
    const latest = items.sort((a, b) => b.id - a.id)[0];
    if (latest && latest.result && latest.result.checklist[idx]) {
      latest.result.checklist[idx].done = done;
      await Storage.saveSubmission(latest);
    }
  }

  async function renderHistory() {
    const items = await Storage.getSubmissions();
    items.sort((a, b) => b.id - a.id);
    if (!items.length) {
      els.historyList.innerHTML = '<div class="empty">暂无记录，去做一次合规自检吧</div>';
      return;
    }
    els.historyList.innerHTML = items.map(it => `
      <div class="history-item" data-id="${it.id}">
        <div class="history-head">
          <span class="history-time">${new Date(it.created_at).toLocaleString()}</span>
          <span class="history-badge ${it.result.risk_level || 'mid'}">${riskText(it.result.risk_level || 'mid')}</span>
        </div>
        <div class="history-text">${esc(it.behavior)}</div>
        <div class="case-meta">${(it.result.standards || []).map(s => s.code).join('、') || '未命中准则'}</div>
      </div>`).join('');

    // 左滑删除（简化：长按删除）
    els.historyList.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('dblclick', async () => {
        if (confirm('删除该条记录？')) {
          await Storage.deleteSubmission(parseInt(item.dataset.id, 10));
          renderHistory();
        }
      });
    });
  }

  els.clearBtn.addEventListener('click', async () => {
    if (confirm('清空全部历史记录？')) {
      await Storage.clearSubmissions();
      renderHistory();
    }
  });

  /* ---------- 导出（打印为 PDF） ---------- */
  els.exportBtn.addEventListener('click', async () => {
    const items = await Storage.getSubmissions();
    if (!items.length) { alert('暂无记录可导出'); return; }
    items.sort((a, b) => a.id - b.id);
    let html = '<h1>CFA 合规自检记录</h1>';
    items.forEach(it => {
      html += `<div style="margin:12px 0;padding:10px;border:1px solid #ccc">
        <strong>${it.created_at}</strong> · ${riskText(it.result.risk_level)}<br>
        ${it.behavior}<br>
        <small>准则：${(it.result.standards || []).map(s => s.code).join('、')}</small>
      </div>`;
    });
    const w = window.open('', '_blank');
    w.document.write(`<html><head><meta charset="utf-8"><title>导出</title></head><body>${html}</body></html>`);
    w.document.close();
    w.print();
  });

  /* ---------- 离线待同步队列 ---------- */
  async function enqueuePending(text) {
    await Storage.savePending({ id: Date.now(), behavior: text, created_at: new Date().toISOString() });
  }
  async function flushPendingQueue() {
    const items = await Storage.getPending();
    for (const it of items) {
      try {
        await API.analyze(it.behavior);
        await Storage.deletePending(it.id);
      } catch (e) { /* 保持待同步 */ }
    }
  }

  /* ---------- 准则速查 ---------- */
  function renderStandards(filter) {
    const f = (filter || '').trim().toLowerCase();
    const entries = Object.entries(window.STANDARD_INFO || {});
    const html = entries
      .map(([code, info]) => {
        const [name, desc] = info;
        const hay = (code + name + desc).toLowerCase();
        if (f && !hay.includes(f)) return '';
        return `<details class="std-card">
          <summary>${code} · ${name}</summary>
          <div class="std-desc">${desc}</div>
        </details>`;
      }).join('');
    els.standardsList.innerHTML = html || '<div class="empty">无匹配准则</div>';
  }
  els.stdSearch.addEventListener('input', () => renderStandards(els.stdSearch.value));

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  function riskText(r) {
    return { high: '高风险', mid: '中风险', low: '低风险' }[r] || '中风险';
  }
  function categoryName(c) {
    return (window.CATEGORIES && window.CATEGORIES[c] && window.CATEGORIES[c].name) || c;
  }

  /* ---------- 初始化 ---------- */
  updateNetState();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
