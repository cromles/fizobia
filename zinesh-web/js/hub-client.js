/**
 * Zinesh web → OAM Hub bağlantı istemcisi
 * Varsayılan: http://127.0.0.1:8787
 * Değiştirmek için: localStorage.setItem('zinesh_hub_api', 'https://hub-api.zinesh.com')
 */
const ZineshHub = (() => {
  const STORAGE_KEY = 'zinesh_hub_api';
  const DEFAULT_API = 'http://127.0.0.1:8787';

  function getApiBase() {
    return (localStorage.getItem(STORAGE_KEY) || DEFAULT_API).replace(/\/$/, '');
  }

  function setApiBase(url) {
    localStorage.setItem(STORAGE_KEY, url.replace(/\/$/, ''));
  }

  async function fetchJson(path) {
    const res = await fetch(`${getApiBase()}${path}`);
    if (!res.ok) throw new Error(`Hub ${path}: ${res.status}`);
    return res.json();
  }

  return {
    getApiBase,
    setApiBase,
    getConfig: () => fetchJson('/hub/sdk/config'),
    getAgents: () => fetchJson('/hub/agents'),
    getLive: () => fetchJson('/hub/live'),
    getVersion: () => fetchJson('/hub/version'),
    async checkConnection() {
      try {
        const cfg = await this.getConfig();
        return { ok: true, config: cfg };
      } catch (err) {
        return { ok: false, error: err.message };
      }
    },
  };
})();
