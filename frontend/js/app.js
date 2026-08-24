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
    stdHints: document.getElementById('std-hints'),
    historyList: document.getElementById('history-list'),
    exportBtn: document.getElementById('export-btn'),
    clearBtn: document.getElementById('clear-history-btn'),
    tabs: document.querySelectorAll('.tab'),
    views: document.querySelectorAll('.view'),
  };

  let currentResult = null;
  const EMAIL_TO = 'eric_han_music@petalmail.com';

  /* ---------- 工具 ---------- */
  function genId(prefix) {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    const ymd = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
    const rand = Math.random().toString(36).slice(2, 6).toUpperCase();
    return `${prefix}-${ymd}-${rand}`;
  }
  function nowText() {
    return new Date().toLocaleString('zh-CN', { hour12: false });
  }
  function openModal(id) {
    document.getElementById(id).hidden = false;
  }
  function closeModal(id) {
    document.getElementById(id).hidden = true;
  }
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.close));
  });
  document.querySelectorAll('.modal-overlay').forEach(ov => {
    ov.addEventListener('click', (e) => { if (e.target === ov) ov.hidden = true; });
  });

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
    if (navigator.onLine) {
      try {
        result = await API.analyze(text);
      } catch (err) {
        // 后端不可达时回退本地
        result = offlineAnalyze(text);
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

    const interceptHtml = risk === 'high' ? `
      <div class="intercept-banner">
        <div class="intercept-title">🚫 合规风险拦截</div>
        <div class="intercept-body">检测到该行为存在明显越界风险，请立即停止相关安排，并完成合规申报以留存记录。</div>
      </div>` : '';

    els.resultArea.innerHTML = `
      ${interceptHtml}
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
      <div class="section-title">合规行动</div>
      <div class="result-actions">
        <button class="primary-btn" id="declare-btn">📩 前往申报（提交申报单）</button>
        <button class="secondary-btn" id="proof-btn">📄 生成合规自证声明</button>
      </div>
    `;

    // 清单勾选交互
    els.resultArea.querySelectorAll('.checklist li').forEach(li => {
      li.addEventListener('click', () => toggleChecklistItem(li));
    });
    const copyBtn = els.resultArea.querySelector('.copy-btn');
    if (copyBtn) copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(r.disclosure_draft).then(() => copyBtn.textContent = '已复制 ✓');
    });

    // 申报 / 自证 按钮
    const declareBtn = els.resultArea.querySelector('#declare-btn');
    if (declareBtn) declareBtn.addEventListener('click', () => openDeclare(r));
    const proofBtn = els.resultArea.querySelector('#proof-btn');
    if (proofBtn) proofBtn.addEventListener('click', () => openProof(r));

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
    const order = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'];
    const groups = {};
    order.forEach(g => { groups[g] = []; });
    entries.forEach(([code, info]) => {
      const major = code.split('(')[0];
      if (groups[major]) groups[major].push([code, info]);
    });
    let html = '';
    let count = 0;
    order.forEach(g => {
      const items = groups[g];
      if (!items || !items.length) return;
      const cards = items.map(([code, info]) => {
        const name = info[0] || '';
        const desc = info[1] || '';
        const aliases = (info[2] || '').split(/[\s,、]+/).filter(Boolean);
        const hay = (code + ' ' + name + ' ' + desc + ' ' + aliases.join(' ')).toLowerCase();
        if (f && !hay.includes(f)) return '';
        count++;
        const tags = aliases.map(a => `<span class="std-tag">${esc(a)}</span>`).join('');
        return `<div class="std-item">
          <div><span class="std-code">${esc(code)}</span><span class="std-name">${esc(name)}</span></div>
          <div class="std-desc">${esc(desc)}</div>
          <div class="std-tags">${tags}</div>
        </div>`;
      }).join('');
      if (cards) html += `<div class="std-group">Standard ${g}</div>${cards}`;
    });
    const countHtml = f
      ? `<div class="std-count">找到 ${count} 条相关准则</div>`
      : `<div class="std-count">共 22 条准则，按 Standard 分组</div>`;
    els.standardsList.innerHTML = (count ? countHtml : '') + html
      || '<div class="empty">无匹配准则，试试「收礼」「内幕」「额外报酬」等关键词</div>';
  }
  els.stdSearch.addEventListener('input', () => renderStandards(els.stdSearch.value));

  /* 可搜关键词提示（可点击直接搜索） */
  const HINT_KEYWORDS = [
    '收礼', '送礼', '招待', '差旅', '内幕', '泄密', '额外报酬', '介绍费',
    '兼职', '离职', '持股', '董事', '研报', '虚假陈述', '个人交易', '抢先', '保密',
  ];
  function renderHints() {
    els.stdHints.innerHTML = '<span class="std-hint-tip">可搜关键词：</span>' +
      HINT_KEYWORDS.map(kw => `<button class="std-hint" data-kw="${kw}">${kw}</button>`).join('');
  }
  els.stdHints.addEventListener('click', (e) => {
    const btn = e.target.closest('.std-hint');
    if (!btn) return;
    els.stdSearch.value = btn.dataset.kw;
    renderStandards(btn.dataset.kw);
  });
  renderHints();

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

  /* ---------- 合规申报 ---------- */
  function openDeclare(r) {
    document.getElementById('d-behavior').value = els.behavior.value.trim();
    document.getElementById('d-standards').value = (r.standards || []).map(s => s.code).join('、') || '未命中';
    document.getElementById('d-risk').value = riskText(r.risk_level || 'mid');
    document.getElementById('d-result').innerHTML = '';
    openModal('declare-modal');
  }

  document.getElementById('d-submit').addEventListener('click', submitDeclare);

  function submitDeclare() {
    const name = document.getElementById('d-name').value.trim();
    const dept = document.getElementById('d-dept').value.trim();
    const behavior = document.getElementById('d-behavior').value.trim();
    const standards = document.getElementById('d-standards').value.trim();
    const risk = document.getElementById('d-risk').value.trim();
    const note = document.getElementById('d-note').value.trim();
    if (!name) { alert('请填写姓名'); return; }
    if (!behavior) { alert('缺少行为描述'); return; }

    const id = genId('SB');
    const time = nowText();
    const actions = (currentResult && currentResult.checklist || []).map(c => c.text).join('；');

    const parts = [
      '致合规部门：', '',
      `本人 ${name}（${dept || '未填写部门'}）现就以下事项进行合规申报：`, '',
      `申报编号：${id}`,
      `申报时间：${time}`,
      `风险等级：${risk}`,
      `涉及准则：${standards}`, '',
      '【行为描述】', behavior,
    ];
    if (note) parts.push('', '【补充说明】', note);
    if (actions) parts.push('', '【拟采取的合规动作】', actions);
    parts.push('', '请合规部门审阅并留存记录。如需进一步信息，请与本人联系。', '', '此致 敬礼', name, time);
    const body = parts.join('\n');
    const subject = `【合规申报】${name} - ${id}`;
    const mailto = `mailto:${EMAIL_TO}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

    document.getElementById('d-result').innerHTML = `
      <div class="declare-box">
        <span class="declare-id">✅ 申报单已生成</span><br>
        申报编号：<strong>${esc(id)}</strong><br>
        申报时间：${esc(time)}<br>
        发送至：${esc(EMAIL_TO)}
      </div>
      <div class="declare-actions">
        <button class="primary-btn" id="d-send">📧 一键发送邮件</button>
        <a class="secondary-btn" href="${mailto}" style="text-decoration:none;text-align:center;display:block">📨 打开邮件客户端发送（备用）</a>
        <button class="secondary-btn" id="d-copy">复制邮件内容</button>
      </div>
      <div id="d-send-status"></div>`;

    document.getElementById('d-send').addEventListener('click', async () => {
      const btn = document.getElementById('d-send');
      btn.disabled = true;
      btn.textContent = '发送中...';
      try {
        await API.sendDeclaration({ name, declaration_id: id, subject, message: body });
        document.getElementById('d-send-status').innerHTML = '<div class="declare-box" style="background:#f0fdf9;border-color:var(--success)"><span class="declare-id">✅ 邮件已发送至合规部</span></div>';
      } catch (err) {
        document.getElementById('d-send-status').innerHTML = `<div class="declare-box" style="background:#fef2f2;border-color:var(--danger)">⚠️ 自动发送不可用（当前未连接后端服务）。请改用下方"打开邮件客户端发送"，或使用局域网演示地址访问。</div>`;
      } finally {
        btn.disabled = false;
        btn.textContent = '📧 一键发送邮件';
      }
    });

    document.getElementById('d-copy').addEventListener('click', () => {
      navigator.clipboard.writeText(body).then(() => document.getElementById('d-copy').textContent = '已复制 ✓');
    });
  }

  /* ---------- 合规自证 ---------- */
  function openProof(r) {
    document.getElementById('p-result').innerHTML = '';
    openModal('proof-modal');
  }

  document.getElementById('p-generate').addEventListener('click', generateProof);

  function generateProof() {
    const name = document.getElementById('p-name').value.trim();
    const matter = document.getElementById('p-matter').value.trim();
    if (!name) { alert('请填写声明人姓名'); return; }
    if (!matter) { alert('请填写声明事项'); return; }

    const id = genId('ZM');
    const time = nowText();
    const doc = [
      '合规自证声明', '',
      `声明编号：${id}`, '',
      `本人 ${name}，现就以下事项作出正式声明：`, '',
      '【声明事项】', matter, '',
      '本人郑重声明：在上述事项中，本人已尽到应有的合规义务，并已于相关行为发生前向有关方面完成了必要的披露与申报。如后续因该事项产生任何合规争议，本声明可作为本人诚信履责的书面凭证。', '',
      `声明人（签字）：${name}`,
      `声明时间：${time}`,
    ].join('\n');

    document.getElementById('p-result').innerHTML = `
      <div class="official-doc">${esc(doc)}</div>
      <div class="declare-actions">
        <button class="secondary-btn" id="p-copy">复制声明内容</button>
        <button class="primary-btn" id="p-print">打印 / 导出 PDF</button>
      </div>`;
    document.getElementById('p-copy').addEventListener('click', () => {
      navigator.clipboard.writeText(doc).then(() => document.getElementById('p-copy').textContent = '已复制 ✓');
    });
    document.getElementById('p-print').addEventListener('click', () => {
      const w = window.open('', '_blank');
      w.document.write(`<html><head><meta charset="utf-8"><title>合规自证声明</title><style>body{font-family:sans-serif;max-width:620px;margin:40px auto;line-height:2;white-space:pre-wrap}</style></head><body>${esc(doc)}</body></html>`);
      w.document.close();
      w.print();
    });
  }

  /* ---------- 初始化 ---------- */
  updateNetState();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
