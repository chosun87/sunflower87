import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { Card, Button } from '@components/PrimeReact';

export default function Login() {
    const navigate = useNavigate();

    const login = useGoogleLogin({
        onSuccess: (tokenResponse) => {
            console.log('Login Success:', tokenResponse);
            
            // 토큰 정보 저장 (gem_gagaebu 스타일 이식)
            const expiryMs = 3600 * 1000; // 1시간
            localStorage.setItem('sunflower87_token', tokenResponse.access_token);
            localStorage.setItem('sunflower87_expiry', Date.now() + expiryMs);
            
            // 대시보드로 이동
            navigate('/dashboard');
        },
        onError: (error) => {
            console.error('Login Failed:', error);
        },
    });

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
