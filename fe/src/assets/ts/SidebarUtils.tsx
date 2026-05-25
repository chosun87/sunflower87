import { type MenuItem, type MenuItemOptions } from '@/assets/ts/PrimeReact';
import { type CustomMenuItem } from '@/data/SidebarData';
import type { NavigateFunction } from 'react-router-dom';

interface CustomMenuItemOptions extends MenuItemOptions {
  active: boolean;
}

export const generateMenuItems = (
  items: CustomMenuItem[],
  currentPath: string,
  navigate: NavigateFunction,
  level = 0
): MenuItem[] => {
  return items.map((item) => {
    const hasChildren = item.children && item.children.length > 0;
    const isChild = level > 0; // 서브링크 계층 판정

    // 2단계 서브 메뉴 액티브 판정
    const isSubActive = isChild && item.data === currentPath;

    // 1단계 부모 메뉴 액티브 판정 (자식 중 현재 경로와 일치하는 노드가 있는지 탐색)
    const isMainActive =
      hasChildren && item.children?.some((child: CustomMenuItem) => child.data === currentPath);

    // 1단계 단일 메뉴 액티브 판정
    const isSingleActive = !isChild && !hasChildren && item.data === currentPath;

    const menuItem: MenuItem = {
      id: item.key,
      label: item.label,
      // 사용자가 유지하길 지시한 icon 및 url 보존 바인딩 규칙 엄격 준수
      icon: item.icon || undefined,
      url: item.data || undefined,
      // 자식인 경우 sidebar-sublink 클래스를 주어 CSS Specificity(우선순위) 압도
      className: isChild
        ? `sidebar-sublink ${isSubActive ? 'active' : ''}`
        : `sidebar-link-container`,
      items: item.children
        ? generateMenuItems(item.children, currentPath, navigate, level + 1)
        : undefined,
      expanded: isMainActive,
      command: (e) => {
        // PrimeReact 기본 템플릿(자식 메뉴)을 사용할 때 url 속성에 의해 발생하는 브라우저 기본 새로고침 방지
        if (e.originalEvent) {
          e.originalEvent.preventDefault();
        }

        if (hasChildren) {
          // 자식이 있는 부모 메뉴는 클릭 시 아코디언이 토글되도록 처리하므로 navigate 생략
          return;
        }
        if (item.data && item.data !== '#') {
          navigate(item.data);
        }
      },
      template: isChild
        ? undefined
        : (modelItem: MenuItem, options: MenuItemOptions) => {
            const opt = options as CustomMenuItemOptions;
            // 1단계 메뉴의 아코디언 전개 상태(opt.active) 또는 경로 매칭 기반 하이라이팅
            const isExpanded = opt.active;
            const activeClass =
              isMainActive || isSingleActive || isExpanded
                ? hasChildren
                  ? 'active-parent'
                  : 'active'
                : '';

            return (
              <div
                className={`p-menuitem-content ${opt.className}`}
                style={{ background: 'transparent', border: 'none' }}
              >
                <a
                  href={modelItem.url || '#'}
                  className={`sidebar-link w-full ${activeClass}`}
                  onClick={(e) => {
                    e.preventDefault(); // 기본 브라우저 새로고침 방지 (SPA 브라우징 보장)
                    if (hasChildren) {
                      opt.onClick(e); // 아코디언 토글 동작 실행
                    } else if (item.data && item.data !== '#') {
                      navigate(item.data); // SPA 이동
                    }
                  }}
                >
                  {modelItem.icon && <i className={`${modelItem.icon} menu-icon`}></i>}
                  <span>{modelItem.label}</span>
                  {item.badge && <span className="sidebar-badge success">{item.badge}</span>}
                  {/* 자식 메뉴가 존재하는 부모 노드의 경우, 전개 상태에 따른 커스텀 chevron 우측 배치 */}
                  {hasChildren && (
                    <i
                      className={`fa-solid ${opt.active ? 'fa-chevron-up' : 'fa-chevron-down'} ml-auto text-xs`}
                      style={{ color: 'var(--sidebar-muted)', order: 2 }}
                    ></i>
                  )}
                </a>
              </div>
            );
          },
    };
    return menuItem;
  });
};
