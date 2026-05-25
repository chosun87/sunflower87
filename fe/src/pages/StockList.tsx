import { BreadCrumb } from '@/assets/ts/PrimeReact';
import { useEffect, useState } from 'react';
import { get } from '@/api/index';
import StockListCmpt from '@/components/StockList/StockListCmpt';

const breadcrumbItems = [{ label: 'Home', url: '/' }, { label: '보유자산' }];

export default function StockList() {
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const res = await get('/api/stocks/portfolio');
        if (res.status === 'success' && res.data) {
          setAccounts(res.data.accounts || []);
        }
      } catch (e) {
        console.error('Failed to load portfolio:', e);
      }
    };
    fetchPortfolio();
  }, []);

  return (
    <main className="page template template-datatable">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">보유 자산</h2>
          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>
        <div className="page-content">
          <StockListCmpt accounts={accounts} />
        </div>
      </div>
    </main>
  );
}
