import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

// 가이드라인에 맞춘 스타일 시트 로드 순서 준수
import 'primereact/resources/themes/lara-light-indigo/theme.css' // 테마
import 'primereact/resources/primereact.min.css' // 코어 CSS
import 'primeicons/primeicons.css' // 아이콘
import 'primeflex/primeflex.css' // 유틸리티 클래스
import '@/assets/css/index.scss' // Pretendard 폰트 등이 포함된 커스텀 Sass

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
