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

const fetchJson = async (path, { method = 'GET', params, body, headers } = {}) => {
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

export const get = (path, params) => fetchJson(path, { method: 'GET', params });
export const post = (path, body) => fetchJson(path, { method: 'POST', body });
export const put = (path, body) => fetchJson(path, { method: 'PUT', body });
export const del = (path) => fetchJson(path, { method: 'DELETE' });

export const getRecommendations = () => get('/api/recommendations');
export const searchStock = (keyword) =>
  get('/api/stocks/search', { keyword: String(keyword || '').trim() });
export const getStockNameByCode = (code) =>
  get('/api/stocks/lookup', { code: String(code || '').trim() });
