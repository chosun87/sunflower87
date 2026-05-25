import { createRoot } from 'react-dom/client';
import App from '@/App';
import packageJson from '@/../package.json';

const APP_NAME = packageJson.name;

// 커스텀 글로벌 Sass 스타일 적용
import '@/assets/css/main.scss';

// PrimeReact Configuration
import 'primeicons/primeicons.css';
import PrimeReact from 'primereact/api';
import { PrimeReactProvider, addLocale } from 'primereact/api';
import { PrimeReact_locale } from '@/assets/ts/PrimeReact';

addLocale('ko', PrimeReact_locale.ko.Calendar);

import { BrowserRouter } from 'react-router-dom';

PrimeReact.ripple = true;

createRoot(document.getElementById('root')!).render(
  // <StrictMode>
  <PrimeReactProvider value={{ ripple: true }}>
    <BrowserRouter basename="/sunflower87">
      <App />
    </BrowserRouter>
  </PrimeReactProvider>
  // </StrictMode>,
);
