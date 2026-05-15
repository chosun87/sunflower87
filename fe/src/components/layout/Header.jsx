import { useNavigate } from 'react-router-dom';
import { Button } from '@components/PrimeReact';

export default function Header() {
    const navigate = useNavigate();
    
    // 임시 isSignedIn 상태 (AuthContext 구현 전까지)
    const isSignedIn = !!localStorage.getItem('sunflower87_token');

    const handleLogout = () => {
        localStorage.removeItem('sunflower87_token');
        localStorage.removeItem('sunflower87_expiry');
        navigate('/login');
    };

    return (
        <header className="app-header">
            <div className="flex align-items-center justify-content-between p-3 bg-primary text-white shadow-2">
                <div className="flex align-items-center gap-2">
                    <i className="pi pi-sun text-2xl"></i>
                    <span className="text-xl font-bold">sunflower87</span>
                </div>
                
                <div className="flex align-items-center gap-3">
                    {isSignedIn && (
                        <Button 
                            label="Logout" 
                            icon="pi pi-sign-out" 
                            className="p-button-text text-white" 
                            onClick={handleLogout} 
                        />
                    )}
                </div>
            </div>
        </header>
    );
}
