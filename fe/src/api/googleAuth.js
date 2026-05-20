import { GOOGLE_AUTH_PARAMS } from '@/assets/js/googleAuthParams';

// GAPI 클라이언트만 초기화 (auth2 제외)
export const initGoogleApi = () => {
  return new Promise((resolve, reject) => {
    if (!window.gapi) {
      reject(new Error('GAPI script not loaded'));
      return;
    }
    window.gapi.load('client', async () => {
      try {
        await window.gapi.client.init({
          discoveryDocs: GOOGLE_AUTH_PARAMS.DISCOVERY_DOCS,
          plugin_name: 'gagaebu',
        });
        resolve();
      } catch (error) {
        console.error('Error initializing GAPI client', error);
        reject(error);
      }
    });
  });
};

// GIS 스크립트 로딩은 @react-oauth/google이 처리하므로 initGoogleAuth는 제거됨

// 새로고침 시 이전에 보관해둔 토큰 주입용
export const setToken = (token) => {
  if (window.gapi && window.gapi.client) {
    window.gapi.client.setToken({ access_token: token });
  }
};

// 로그아웃 및 토큰 권한 취소
export const signOut = () => {
  return new Promise((resolve) => {
    if (!window.gapi || !window.gapi.client) {
      resolve();
      return;
    }
    const token = window.gapi.client.getToken();
    if (token !== null) {
      window.google.accounts.oauth2.revoke(token.access_token, () => {
        window.gapi.client.setToken('');
        resolve();
      });
    } else {
      resolve();
    }
  });
};
