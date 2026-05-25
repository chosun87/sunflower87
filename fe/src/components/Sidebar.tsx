import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { PanelMenu } from '@/assets/ts/PrimeReact'
import { menuData } from '@/data/SidebarData'
import packageJson from '@/../package.json'
import reactLogo from '@/assets/image/react.svg'

interface SidebarProps {
  collapsed: boolean
}

import { generateMenuItems } from '@/assets/ts/SidebarUtils'

export default function Sidebar({ collapsed }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const currentPath = location.pathname

  // menuData를 PrimeReact PanelMenu 규격인 MenuItem[]으로 변환 및 최적화 메모이제이션(useMemo) 캐싱
  const memoizedMenuGroups = useMemo(() => {
    // 그룹별 전체 데이터 사전 컴파일 수행 및 메모이제이션 반환
    return menuData.map((group) => ({
      title: group.title,
      items: generateMenuItems(group.items, currentPath, navigate),
    }))
  }, [currentPath, navigate])

  return (
    <aside className={`app-sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* 1. 사이드바 로고 영역 - package.json의 name과 version 동적 로딩 출력 */}
      <div className="sidebar-header">
        <a href="/" className="logo">
          <img src={reactLogo} alt="Gem Dashboard logo" className="sidebar-logo-icon" />
          <span className="app-name">
            {packageJson.name.replace(/_/g, ' ')}
            <span className="app-version">v{packageJson.version}</span>
          </span>
        </a>
      </div>

      {/* 2. 사이드바 메뉴 영역 - useMemo 캐시를 그대로 끌어와 렌더링 오버헤드 0 실현 */}
      <div className="sidebar-menu-wrapper">
        {memoizedMenuGroups.map((group, index) => (
          <div key={index} className="menu-group">
            <h3 className="menu-group-title">{group.title}</h3>
            <PanelMenu model={group.items} multiple className="sidebar-panelmenu" />
          </div>
        ))}
      </div>
    </aside>
  )
}
