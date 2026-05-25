import { useState } from 'react';
import {
  Button,
  Panel,
  type PanelProps,
  type PanelHeaderTemplateOptions,
} from '@/assets/ts/PrimeReact';

export interface CustomPanelProps extends PanelProps {
  maximizable?: boolean;
}

export default function CustomPanel({
  maximizable = false,
  header,
  headerTemplate,
  children,
  className = '',
  ...props
}: CustomPanelProps) {
  const [maximized, setMaximized] = useState(false);

  // maximizable 속성이 true이거나 headerTemplate이 존재하는 경우에 동적 헤더 제어 적용
  const resolvedHeaderTemplate = (options: PanelHeaderTemplateOptions) => {
    if (headerTemplate) {
      return typeof headerTemplate === 'function' ? headerTemplate(options) : headerTemplate;
    }

    if (maximizable) {
      const combinedClassName = `${options.className} align-items-center w-full`;

      // header 속성이 문자열이거나 ReactNode인 경우 수평 정합 처리
      const headerContent =
        typeof header === 'string' ? <span className="panel-header-title">{header}</span> : header;

      return (
        <div className={combinedClassName}>
          <div className="p-panel-title">{headerContent}</div>
          <div className="panel-header-actions">
            {/* 더보기 버튼은 Maximize 바로 왼쪽에 배치 */}
            <Button
              icon="fa-solid fa-ellipsis-vertical"
              rounded
              text
              severity="secondary"
              onClick={() =>
                alert(
                  `[${typeof header === 'string' ? header : '패널'}] 더보기 옵션이 활성화되었습니다.`
                )
              }
              title="더보기"
            />
            <Button
              icon="fa-solid fa-expand"
              rounded
              text
              severity="secondary"
              onClick={() => setMaximized(!maximized)}
              title="전체화면"
            />
          </div>
        </div>
      );
    }

    // maximizable이나 headerTemplate이 없으면 PrimeReact가 기본으로 처리
    return undefined;
  };

  const hasTemplate = maximizable || headerTemplate;
  const panelClassName = `custom-panel ${className}`;

  return (
    <Panel
      className={panelClassName + (maximized ? 'maximized' : '')}
      header={hasTemplate ? undefined : header}
      headerTemplate={hasTemplate ? resolvedHeaderTemplate : undefined}
      {...props}
    >
      {children}
    </Panel>
  );
}
