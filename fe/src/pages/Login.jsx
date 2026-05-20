import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button } from '@/assets/js/PrimeReact';
import { useAuth } from '@/context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login, isSignedIn, isInitialized } = useAuth();

  useEffect(() => {
    if (isInitialized && isSignedIn) {
      navigate('/dashboard');
    }
  }, [isInitialized, isSignedIn, navigate]);

  return (
    <div className="flex align-items-center justify-content-center min-h-screen bg-gray-100">
      <Card className="shadow-4 border-round p-4" style={{ width: '400px' }}>
        <div className="text-center mb-6">
          <i className="pi pi-sun text-6xl text-primary mb-3"></i>
          <h1 className="text-3xl font-bold m-0">sunflower87</h1>
          <p className="text-600 mt-2">Personal Financial Dashboard</p>
        </div>

        <div className="flex flex-column gap-4">
          <Button
            label="Google 계정으로 로그인"
            icon="pi pi-google"
            className="p-button-raised w-full"
            onClick={() => login()}
          />

          <div className="text-center text-500 text-sm">
            Decision Maker: <span className="font-bold">SUN</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
