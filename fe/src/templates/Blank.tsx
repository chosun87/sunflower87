import { BreadCrumb } from '@/assets/ts/PrimeReact';

const breadcrumbItems = [{ label: 'Home', url: '/' }, { label: 'Templates' }, { label: 'Blank' }];

export default function TemplateBlank() {
  return (
    <main className="page template template-blank">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">Blank</h2>

          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>

        <div className="page-content">
          <p>이 페이지는 새로운 템플릿을 만들 때 시작점으로 사용할 수 있는 빈 페이지입니다.</p>
          <p>원하는 컴포넌트를 추가하여 나만의 대시보드를 만들어보세요!</p>
        </div>
      </div>
    </main>
  );
}
