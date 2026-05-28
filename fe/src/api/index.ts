const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

const buildUrl = (path, params) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = API_BASE
    ? new URL(`${API_BASE}${normalizedPath}`)
    : new URL(normalizedPath, window.location.origin);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
};

const handleResponse = async (response) => {
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    const message = data?.message || data?.detail || response.statusText;
    throw new Error(message || 'API 요청에 실패했습니다.');
  }

  return data;
};

const fetchJson = async (path: any, { method = 'GET', params, body, headers }: any = {}) => {
  const url = buildUrl(path, params);
  const fetchOptions = {
    method,
    headers: {
      ...headers,
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  };

  const response = await fetch(url, fetchOptions);
  return handleResponse(response);
};

export const get = (path: any, params?: any) => fetchJson(path, { method: 'GET', params });
export const post = (path: any, body?: any) => fetchJson(path, { method: 'POST', body });
export const put = (path: any, body?: any) => fetchJson(path, { method: 'PUT', body });
export const del = (path: any) => fetchJson(path, { method: 'DELETE' });

export const getRecommendations = () => get('/api/recommendations');
export const searchStock = (keyword?: string) =>
  get('/api/stocks/search', { keyword: String(keyword || '').trim() });
export const getStockNameByCode = (code?: string) =>
  get('/api/stocks/lookup', { code: String(code || '').trim() });
export const getDashboardKpi = (acc_cd?: string) =>
  get(`/api/dashboard/kpi${acc_cd ? `?acc_cd=${acc_cd}` : ''}`);

export const syncDailyBalance = () => post('/api/settings/sync-daily-balance', {});
