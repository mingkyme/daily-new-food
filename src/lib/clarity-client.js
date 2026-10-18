// Included inline only when a real project ID is configured at build time.
(() => {
  const panel = document.querySelector('[data-clarity-project-id]');
  const id = panel?.dataset.clarityProjectId;
  if (!id || !/^[a-z0-9]+$/.test(id)) return;
  const key = 'food-clarity-consent-v1';
  const maxAge = 180 * 24 * 60 * 60 * 1000;
  let script;
  const status = panel.querySelector('[role="status"]');
  function remember(granted) {
    try {
      window.localStorage.setItem(key, JSON.stringify({ granted, at: Date.now() }));
    } catch {
      // A quota error must not leave an older grant in place after revocation.
      try { window.localStorage.removeItem(key); } catch { /* Storage blocked; reads fail closed too. */ }
    }
  }
  function allowed() {
    try {
      const value = JSON.parse(window.localStorage.getItem(key) || 'null');
      const age = Date.now() - value?.at;
      return value?.granted === true && age >= 0 && age < maxAge;
    } catch { return false; }
  }
  function grant() {
    if (script) return;
    window.clarity = function (...args) { window.clarity.q.push(args); };
    window.clarity.q = [];
    window.clarity('consentv2', { analytics_Storage: 'granted', ad_Storage: 'denied' });
    script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.clarity.ms/tag/' + id;
    document.head.append(script);
    status.textContent = 'Clarity 분석 허용됨';
  }
  function deny() {
    status.textContent = 'Clarity 분석 거부됨';
    if (!script) return;
    window.clarity('consentv2', { analytics_Storage: 'denied', ad_Storage: 'denied' });
    // consentv2 denial alone still permits cookieless collection. Unload
    // the document, rather than pretending removing a script stops its SDK.
    script.remove();
    for (const name of ['_clck', '_clsk']) {
      const parts = window.location.hostname.split('.');
      const domains = ['', ...parts.map((_, i) => '; Domain=' + parts.slice(i).join('.'))];
      for (const domain of domains) document.cookie = name + '=; Max-Age=0; Path=/' + domain + '; SameSite=Lax';
    }
    window.location.reload();
  }
  panel.querySelector('[data-clarity-grant]').addEventListener('click', () => { remember(true); grant(); });
  panel.querySelector('[data-clarity-deny]').addEventListener('click', () => { remember(false); deny(); });
  window.addEventListener('storage', event => { if ((event.key === key || event.key === null) && !allowed()) deny(); });
  window.addEventListener('pageshow', event => { if (event.persisted && script && !allowed()) deny(); });
  if (allowed()) grant();
})();
