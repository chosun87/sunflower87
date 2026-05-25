import packageJson from '@/../package.json'

const APP_NAME = packageJson.name

export const GOOGLE_AUTH_PARAMS = {
  SRC: 'https://accounts.google.com/gsi/client',
  CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID,
  SCOPES: 'https://www.googleapis.com/auth/spreadsheets',
  DISCOVERY_DOCS: ['https://sheets.googleapis.com/$discovery/rest?version=v4'],
  REDIRECT_URI: `http://localhost:3000/${APP_NAME}`, // 로컬 및 Github Pages 배포 경로 고려

  // 인증 관련
  TOKEN_KEY: `${APP_NAME}_token`,
  EXPIRY_KEY: `${APP_NAME}_expiry`,
  EXTENSION_THRESHOLD_SEC: 180, // 3분 전
  TOKEN_EXPIRY_MIN: 60, // 구글 api에서 토큰을 리프레쉬하는 시간: 최대 60분
  DISABLED_RELOGIN: false, // 재로그인 비활성화
};
