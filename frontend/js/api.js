/* 后端 API 调用封装 */
const API = (() => {
  // 可通过 localStorage 覆盖后端地址
  let baseUrl = localStorage.getItem('api_base_url') || '';
  function setBaseUrl(url) { baseUrl = url; localStorage.setItem('api_base_url', url); }
  function getBaseUrl() { return baseUrl; }

  async function analyze(behavior) {
    const url = baseUrl ? `${baseUrl}/api/analyze` : '/api/analyze';
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ behavior }),
    });
    if (res.status === 429) throw new Error('请求过于频繁，请稍后再试');
    if (!res.ok) throw new Error(`服务错误 (${res.status})`);
    return res.json();
  }

  async function health() {
    const url = baseUrl ? `${baseUrl}/health` : '/health';
    const res = await fetch(url);
    return res.ok ? res.json() : null;
  }

  async function sendDeclaration(payload) {
    const url = baseUrl ? `${baseUrl}/api/send-declaration` : '/api/send-declaration';
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`发送失败 (${res.status})`);
    return res.json();
  }

  async function polish(behavior) {
    const url = baseUrl ? `${baseUrl}/api/polish` : '/api/polish';
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ behavior }),
    });
    if (!res.ok) throw new Error(`转写失败 (${res.status})`);
    return res.json();
  }

  return { analyze, health, sendDeclaration, polish, setBaseUrl, getBaseUrl };
})();
