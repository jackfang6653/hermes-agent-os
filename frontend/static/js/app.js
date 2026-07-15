/* Hermes OS Dashboard — Application */
const API = '/api';
let currentPage = 'dashboard';

// ── Navigation ──
document.querySelectorAll('[data-page]').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    switchPage(el.dataset.page);
  });
});

function switchPage(page) {
  currentPage = page;
  document.querySelectorAll('[data-page]').forEach(el => {
    el.classList.toggle('nav-active', el.dataset.page === page);
  });
  renderPage(page);
}

const PAGE_INFO = {
  dashboard: { title: '仪表盘', desc: '系统概览与统计数据' },
  research:  { title: '品牌研究', desc: '输入品牌名进行自动研究分析' },
  brands:    { title: '品牌DNA', desc: '已研究的品牌档案与视觉DNA' },
  generate:  { title: '生成', desc: '生成品牌详情页图片' },
  knowledge: { title: '知识库', desc: '设计模式库与4A案例' },
  evolution: { title: '进化', desc: '品牌DNA自进化引擎' },
};

function renderPage(page) {
  const info = PAGE_INFO[page] || PAGE_INFO.dashboard;
  document.getElementById('page-title').textContent = info.title;
  document.getElementById('page-desc').textContent = info.desc;
  const container = document.getElementById('page-content');
  container.innerHTML = '<div class="flex items-center justify-center py-20"><div class="spinner mr-3"></div>加载中...</div>';
  
  switch(page) {
    case 'dashboard': renderDashboard(container); break;
    case 'research':  renderResearch(container); break;
    case 'brands':    renderBrandList(container); break;
    case 'generate':  renderGenerate(container); break;
    case 'knowledge': renderKnowledge(container); break;
    case 'evolution': renderEvolution(container); break;
  }
}

// ── API helper ──
async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: {'Content-Type': 'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  return r.json();
}

// ═══════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════
async function renderDashboard(container) {
  const data = await api('/status');
  const db = data.database || {};
  
  container.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      ${[
        ['📊', db.brands || 0, '品牌档案'],
        ['📚', db.knowledge || 0, '设计知识'],
        ['🎨', db.patterns || 0, '设计模式'],
        ['🏷️', db.tokens || 0, '设计令牌'],
        ['🏢', db.agency_cases || 0, '4A案例'],
        ['🔄', db.evolution_log || 0, '进化次数'],
      ].map(([icon, val, label]) => `
        <div class="card text-center">
          <div class="text-2xl mb-1">${icon}</div>
          <div class="stat-value">${val}</div>
          <div class="stat-label">${label}</div>
        </div>
      `).join('')}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="font-semibold text-gray-800 dark:text-white mb-4">📡 快速操作</h3>
        <div class="space-y-3">
          <button onclick="switchPage('research')" class="btn btn-primary w-full">🔍 研究新品牌</button>
          <button onclick="switchPage('generate')" class="btn btn-secondary w-full">🖼️ 生成详情页</button>
          <button onclick="switchPage('evolution')" class="btn btn-secondary w-full">🔄 运行自进化</button>
        </div>
      </div>
      <div class="card">
        <h3 class="font-semibold text-gray-800 dark:text-white mb-4">⚙️ 系统状态</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">Pipeline</span><span class="badge badge-green">${data.pipeline || 'HermesPipeline'}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">输出目录</span><span class="text-gray-700 dark:text-gray-300">${data.output_dir || '-'}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">数据库</span><span class="text-gray-700 dark:text-gray-300">unified_brand.db</span></div>
        </div>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════
// RESEARCH
// ═══════════════════════════════════════════════════════
function renderResearch(container) {
  container.innerHTML = `
    <div class="card mb-6">
      <div class="flex gap-4">
        <input id="research-brand" class="input flex-1" placeholder="输入品牌名，如：MUJI 無印良品">
        <select id="research-cat" class="input w-48">
          <option value="furniture">家具</option>
          <option value="fashion">时尚</option>
          <option value="electronics">电子</option>
          <option value="food">食品</option>
          <option value="other">其他</option>
        </select>
        <button onclick="runResearch()" class="btn btn-primary whitespace-nowrap">🔍 开始研究</button>
      </div>
    </div>
    <div id="research-result" class="space-y-4"></div>`;
}

async function runResearch() {
  const brand = document.getElementById('research-brand').value.trim();
  const cat = document.getElementById('research-cat').value;
  if (!brand) return alert('请输入品牌名');
  
  const el = document.getElementById('research-result');
  el.innerHTML = '<div class="card text-center py-10"><div class="spinner mx-auto mb-3"></div><p class="text-gray-500">研究中...</p></div>';
  
  const r = await api('/research', 'POST', { brand, category: cat });
  
  el.innerHTML = `
    <div class="card">
      <h3 class="font-semibold text-gray-800 dark:text-white mb-3">✅ 研究完成</h3>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between"><span class="text-gray-500">品牌</span><span>${r.brand || brand}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">状态</span><span>${Object.entries(r.stages || {}).map(([k,v]) => `${k}: ${v}`).join(', ')}</span></div>
        ${r.output?.zip ? `<div class="flex justify-between"><span class="text-gray-500">输出</span><a href="#" class="text-blue-600 hover:underline">📦 查看ZIP</a></div>` : ''}
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════
// BRAND LIST
// ═══════════════════════════════════════════════════════
async function renderBrandList(container) {
  const data = await api('/brands');
  const brands = data.brands || [];
  
  container.innerHTML = `
    <div class="mb-4"><input id="brand-search" class="input max-w-md" placeholder="搜索品牌..." oninput="filterBrands()"></div>
    <div id="brand-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      ${brands.length ? brands.map(b => `
        <div class="card brand-card cursor-pointer hover:shadow-lg transition-shadow" onclick="showBrand('${b.name}')">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold text-gray-800 dark:text-white">${b.name}</h3>
            <span class="badge badge-blue">${b.category || '通用'}</span>
          </div>
          <div class="text-sm text-gray-500">研究 ${b.research_count || 0} 次</div>
        </div>
      `).join('') : '<div class="col-span-3 card text-center py-10 text-gray-500">暂无品牌数据</div>'}
    </div>
    <div id="brand-detail" class="mt-6"></div>`;
}

function filterBrands() {
  const q = document.getElementById('brand-search').value.toLowerCase();
  document.querySelectorAll('.brand-card').forEach(el => {
    el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

async function showBrand(name) {
  const el = document.getElementById('brand-detail');
  el.innerHTML = '<div class="card"><div class="spinner mx-auto"></div></div>';
  const data = await api('/brand/' + encodeURIComponent(name));
  
  el.innerHTML = `
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white">${name}</h3>
        <button onclick="document.getElementById('brand-detail').innerHTML=''" class="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      ${data.brand ? `
        <div class="grid grid-cols-2 gap-4 text-sm mb-4">
          <div><span class="text-gray-500">品类:</span> ${data.brand.category || '-'}</div>
          <div><span class="text-gray-500">研究次数:</span> ${data.brand.research_count || 0}</div>
        </div>
      ` : '<p class="text-gray-500">无详细档案</p>'}
      ${data.knowledge?.length ? `
        <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">设计知识 (${data.knowledge.length}条)</h4>
        <div class="space-y-2 max-h-60 overflow-y-auto">
          ${data.knowledge.slice(0, 10).map(k => `
            <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm">
              <span class="badge badge-gray mb-1">${k.type}</span>
              <p class="text-gray-600 dark:text-gray-300">${typeof k.content === 'string' ? k.content.slice(0, 200) : JSON.stringify(k.content).slice(0, 200)}</p>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>`;
}

// ═══════════════════════════════════════════════════════
// GENERATE
// ═══════════════════════════════════════════════════════
function renderGenerate(container) {
  container.innerHTML = `
    <div class="card mb-6">
      <div class="flex gap-4">
        <input id="gen-brand" class="input flex-1" placeholder="品牌名，如：NORHOR" value="NORHOR">
        <select id="gen-cat" class="input w-48">
          <option value="furniture">家具</option>
          <option value="fashion">时尚</option>
          <option value="electronics">电子</option>
          <option value="food">食品</option>
          <option value="other">其他</option>
        </select>
        <button onclick="runGenerate()" class="btn btn-primary whitespace-nowrap">🖼️ 生成</button>
      </div>
    </div>
    <div id="gen-result"></div>`;
}

async function runGenerate() {
  const brand = document.getElementById('gen-brand').value.trim();
  const cat = document.getElementById('gen-cat').value;
  if (!brand) return alert('请输入品牌名');
  
  const el = document.getElementById('gen-result');
  el.innerHTML = '<div class="card text-center py-10"><div class="spinner mx-auto mb-3"></div><p class="text-gray-500">生成中...</p></div>';
  
  const r = await api('/generate', 'POST', { brand, category: cat });
  
  el.innerHTML = `
    <div class="card">
      <h3 class="font-semibold text-gray-800 dark:text-white mb-3">✅ 生成完成</h3>
      <div class="text-sm space-y-2">
        <p>品牌: ${r.brand || brand}</p>
        <p>${r.output?.zip ? `📦 ZIP: <code class="text-blue-600">${r.output.zip}</code>` : ''}</p>
        <p>状态: ${Object.entries(r.stages || {}).map(([k,v]) => `${k}: ${v}`).join(' | ')}</p>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════
// KNOWLEDGE
// ═══════════════════════════════════════════════════════
async function renderKnowledge(container) {
  const data = await api('/knowledge');
  const s = data.stats || {};
  
  container.innerHTML = `
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="card text-center"><div class="stat-value">${s.patterns || 0}</div><div class="stat-label">设计模式</div></div>
      <div class="card text-center"><div class="stat-value">${s.brands || 0}</div><div class="stat-label">品牌</div></div>
      <div class="card text-center"><div class="stat-value">${s.agency_cases || 0}</div><div class="stat-label">4A案例</div></div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="font-semibold text-gray-800 dark:text-white mb-3">🎨 设计模式</h3>
        <div class="space-y-2 max-h-80 overflow-y-auto">
          ${(data.patterns || []).map(p => `
            <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div class="flex items-center gap-2 mb-1">
                <span class="badge badge-blue">${p.category}</span>
                <span class="font-medium text-gray-800 dark:text-white text-sm">${p.name}</span>
              </div>
              <p class="text-xs text-gray-500">${(p.description || '').slice(0, 100)}</p>
            </div>
          `).join('') || '<p class="text-gray-500 text-sm">暂无模式</p>'}
        </div>
      </div>
      <div class="card">
        <h3 class="font-semibold text-gray-800 dark:text-white mb-3">🏢 4A案例</h3>
        <div class="space-y-2 max-h-80 overflow-y-auto">
          ${(data.agency_cases || []).map(c => `
            <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div class="font-medium text-gray-800 dark:text-white text-sm">${c.agency}</div>
              <p class="text-xs text-gray-500">${c.project || c.rationale || ''}</p>
            </div>
          `).join('') || '<p class="text-gray-500 text-sm">暂无案例</p>'}
        </div>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════
// EVOLUTION
// ═══════════════════════════════════════════════════════
function renderEvolution(container) {
  container.innerHTML = `
    <div class="card mb-6">
      <h3 class="font-semibold text-gray-800 dark:text-white mb-3">🔄 品牌DNA自进化</h3>
      <p class="text-sm text-gray-500 mb-4">研究顶尖4A公司设计案例，自动学习并丰富品牌DNA库</p>
      <div class="flex gap-3">
        <button onclick="runEvolution()" class="btn btn-primary">🚀 运行进化周期</button>
        <button onclick="renderEvolutionResult('history')" class="btn btn-secondary">📋 查看历史</button>
      </div>
    </div>
    <div id="evolution-result"></div>`;
}

async function runEvolution() {
  const el = document.getElementById('evolution-result');
  el.innerHTML = '<div class="card text-center py-10"><div class="spinner mx-auto mb-3"></div><p class="text-gray-500">运行自进化 (约30秒)...</p></div>';
  
  try {
    const r = await api('/evolution', 'POST');
    const steps = r.steps || {};
    el.innerHTML = `
      <div class="card">
        <h3 class="font-semibold text-gray-800 dark:text-white mb-3">✅ 进化完成</h3>
        <div class="space-y-2 text-sm">
          ${Object.entries(steps).map(([k,v]) => `
            <div class="flex justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
              <span>${k}</span><span>${typeof v === 'string' && v.includes('✅') ? '✅' : v}</span>
            </div>
          `).join('')}
          ${r.total_cases !== undefined ? `<div class="mt-3 p-3 bg-blue-50 dark:bg-blue-900 rounded text-sm">累计案例: ${r.total_cases}</div>` : ''}
        </div>
      </div>`;
  } catch(e) {
    el.innerHTML = `<div class="card text-red-500">❌ 进化失败: ${e.message}</div>`;
  }
}

// ═══════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════
function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
}

// Init
if (localStorage.getItem('theme') === 'dark') document.documentElement.classList.add('dark');
switchPage('dashboard');
