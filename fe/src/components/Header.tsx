import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Avatar, Button, InputText, Menubar, Menu, type MenuItem } from '@/assets/ts/PrimeReact'
import { showConfirm } from '@/assets/ts/dialogUtils'
import { useAuth, useAuthTimer } from '@/context/AuthContext'
import avatarImg from '@/assets/image/avatar.jpg'

interface HeaderProps {
  isDarkMode: boolean
  toggleTheme: () => void
  toggleSidebar: () => void
}

export default function Header({ isDarkMode, toggleTheme, toggleSidebar }: HeaderProps) {
  const navigate = useNavigate()
  const { logout, extendLogin } = useAuth()
  const { authRemainingTime } = useAuthTimer()

  const handleLogout = () => {
    showConfirm({
      header: '로그아웃 확인',
      message: '로그아웃 하시겠습니까?',
      acceptLabel: '로그아웃',
      accept: async () => {
        await logout()
        navigate('/login')
      },
    })
  }

  // Menubar의 중간 영역에 배치할 가로 탐색 메뉴 모델 (사용자 참고 스니펫 구조 반영)
  const menuItems: MenuItem[] = []
  // 프로필 드롭다운 메뉴용 팝업 참조 및 메뉴 아이템
  const profileMenuRef = useRef<Menu>(null)
  const profileMenuItems: MenuItem[] = [
    ...((authRemainingTime !== '00:00')
      ? [
          {
            label: `인증 연장`,
            icon: 'fa-solid fa-clock-rotate-left',
            command: () => {
              extendLogin()
            },
          },
        ]
      : []),
    {
      label: '로그아웃',
      icon: 'fa-solid fa-arrow-right-from-bracket',
      command: () => {
        handleLogout()
      },
    },
    { separator: true } as MenuItem,
    {
      label: '내 프로필',
      icon: 'fa-solid fa-user',
      disabled: true,
      command: () => {
        alert('프로필 페이지로 이동합니다.')
      },
    },
    {
      label: '설정',
      icon: 'fa-solid fa-gear',
      disabled: true,
      command: () => {
        alert('설정 화면을 엽니다.')
      },
    },
  ]

  // Menubar의 좌측 템플릿 (사이드바 토글 버튼 및 검색창)
  const startTemplate = (
    <div className="header-left mr-4">
      <Button
        icon="fa-solid fa-bars-staggered"
        rounded
        text
        severity="secondary"
        className="sidebar-toggle-btn"
        onClick={toggleSidebar}
        aria-label="Toggle Sidebar"
      />
      <div className="p-inputgroup flex-1 ml-2">
        <InputText placeholder="종목 코드, 자산 검색..." />
        <Button icon="fa-solid fa-search" className="p-button-primary" />
      </div>
    </div>
  )

  // Menubar의 우측 템플릿 (테마 스위처 및 유저 아바타 그룹)
  const endTemplate = (
    <div className="header-right ml-4">
      {/* Light/Dark 테마 스위치 */}
      <Button
        icon={isDarkMode ? 'fa-solid fa-sun hover-scale' : 'fa-solid fa-moon hover-scale'}
        rounded
        text
        severity="secondary"
        className="theme-toggle-btn"
        tooltip={isDarkMode ? `Light모드로 변경` : `Dark모드로 변경`}
        tooltipOptions={{ position: 'left' }}
        onClick={toggleTheme}
        aria-label="Toggle Theme"
      />

      <Button
        rounded
        text
        severity="secondary"
        className="user-profile-btn ml-2"
        tooltip={(authRemainingTime !== '00:00') ? `인증 만료까지 남은 시간: ${authRemainingTime}` : '인증 정보 없음'}
        tooltipOptions={{ position: 'left' }}
        onClick={(e) => profileMenuRef.current?.toggle(e)}
        aria-controls="profile_popup_menu"
        aria-haspopup
      >
        <Avatar
          image={avatarImg}
          shape="circle"
          size="normal"
        />
        <span
          className="auth-remaining-time text-xs monospace"
        >
          {authRemainingTime}
        </span>
        <i className="fa-solid fa-chevron-down ml-2"></i>
      </Button>

      {/* 프로필 팝업 메뉴 컴포넌트 */}
      <Menu model={profileMenuItems} popup ref={profileMenuRef} id="profile_popup_menu" />
    </div>
  )

  return (
    <header className="w-full">
      {/* start, model, end를 한 번에 결합하여 완벽한 엔터프라이즈 navbar 구조 구축 */}
      <Menubar model={menuItems} start={startTemplate} end={endTemplate} className="app-header" />
    </header>
  )
}
