import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';

// 시맨틱 레이아웃을 위한 컴포넌트 로드
import Header from '@components/layout/Header';
import Footer from '@components/layout/Footer';

// 주요 페이지 컴포넌트 다이나믹 로딩 (Lazy Loading) 적용
const Login = lazy(() => import('@/pages/Login'));
const Dashboard = lazy(() => import('@/pages/Dashboard'));

function App() {
  // .env 환경변수에서 구글 클라이언트 ID 로드
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <Router>
        <div className="app-container flex flex-column min-h-screen">
          
          {/* Header 컴포넌트 내부에서 <header> 태그 관리 */}
          <Header />

          {/* SUN님 지시사항: HTML Semantics <main> 및 다이나믹 로딩 래퍼 적용 */}
          <main className="app-content flex-grow-1">
            <Suspense fallback={<div className="p-4 text-center">🌻 sunflower87 로딩 중...</div>}>
              <Routes>
                {/* 메뉴 라우팅 설정 */}
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<Dashboard />} />
                
                {/* 기본 경로 접근 시 로그인 또는 대시보드로 리다이렉트 */}
                <Route path="*" element={<Navigate to="/login" replace />} />
              </Routes>
            </Suspense>
          </main>

          {/* Footer 컴포넌트 내부에서 <footer> 태그 관리 */}
          <Footer />

        </div>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;
