import { useState, useEffect, lazy, Suspense } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'

import themeDark from 'primereact/resources/themes/md-dark-indigo/theme.css?url'
import themeLight from 'primereact/resources/themes/md-light-indigo/theme.css?url'

import Layout from '@components/Layout'
import AuthGuard from '@components/AuthGuard'

const Login = lazy(() => import('@/pages/Login'))

const Dashboard = lazy(() => import('@/pages/Dashboard')) //Dashboard
const StockList = lazy(() => import('@/pages/StockList'))       //보유 자산

const TemplateBlank = lazy(() => import('@/templates/Blank'))
const TemplateDataTable = lazy(() => import('@/templates/DataTable'))

function AppContent() {
  const location = useLocation()
  const isLoginPage = location.pathname === '/login'

  // 기획 사양: 기본(default)은 Light 모드 구동
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    // 1. body 태그에 theme 클래스 바인딩 (Sass variables 및 스타일 분기용)
    if (isDarkMode) {
      document.documentElement.classList.remove('light-mode')
      document.documentElement.classList.add('dark-mode')
    } else {
      document.documentElement.classList.remove('dark-mode')
      document.documentElement.classList.add('light-mode')
    }

    // 2. index.html의 theme-link 스타일시트 href 경로 실시간 스위칭
    const themeLink = document.getElementById('theme-link') as HTMLLinkElement
    if (themeLink) {
      themeLink.href = isDarkMode ? themeDark : themeLight
    }
  }, [isDarkMode])

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode)
  }

  const renderFallback = () => {
    return (
      <main className="page full-page">
        <div className="p-4 text-center">
          🌻 sunflower87 로딩 중...
        </div>
      </main>
    )
  }

  const pageContent = (
    <Suspense fallback={renderFallback()}>
      <Routes>
        {/* Public Route */}
        <Route path="/login" element={<Login />} />

        {/* Unknown routes redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />

        {/* Protected Routes wrapped by AuthGuard */}
        <Route element={<AuthGuard />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 메뉴 라우팅 설정 */}
          {/* Dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />
          {/* 보유 자산 */}
          <Route path="/stockList" element={<StockList />} />
        </Route>

        {/* Template Pages */}
        <Route path="/templates/blank" element={<TemplateBlank />} />
        <Route path="/templates/datatable" element={<TemplateDataTable />} />
      </Routes>
    </Suspense>
  )

  if (isLoginPage) {
    return pageContent
  }

  return (
    <Layout isDarkMode={isDarkMode} toggleTheme={toggleTheme}>
      {pageContent}
    </Layout>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
