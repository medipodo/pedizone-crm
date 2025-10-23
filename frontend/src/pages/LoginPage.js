import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { axiosInstance } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Lock, User } from 'lucide-react';

const LoginPage = ({ setUser }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axiosInstance.post('/auth/login', { username, password });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      setUser(response.data.user);
      toast.success('Giriş başarılı!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleInitialize = async () => {
    setInitializing(true);
    try {
      const response = await axiosInstance.post('/init');
      toast.success(response.data.message);
      if (response.data.admin_username) {
        toast.info(`Admin: ${response.data.admin_username} / ${response.data.admin_password}`);
        setUsername(response.data.admin_username);
        setPassword(response.data.admin_password);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Başlatma başarısız');
    } finally {
      setInitializing(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-white via-red-50 to-white p-4" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl p-8 space-y-6 border border-gray-100">
          {/* Logo */}
          <div className="text-center space-y-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_f2a1a2de-506c-4346-999f-22d1252f1d2d/artifacts/oi6kp97t_PediZone.png" 
              alt="PediZone" 
              className="h-60 mx-auto mb-6"
            />
            <h1 className="text-2xl font-bold text-gray-900">PediZone'a Hoş Geldiniz</h1>
            <p className="text-gray-500 text-sm">İş Takip ve Saha Satış Sistemi</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-700 font-medium">Kullanıcı Adı</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <Input
                  id="username"
                  type="text"
                  placeholder="Kullanıcı adınızı girin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10 h-12 border-gray-200 focus:border-[#E50019]"
                  data-testid="username-input"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-700 font-medium">Şifre</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <Input
                  id="password"
                  type="password"
                  placeholder="Şifrenizi girin"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 h-12 border-gray-200 focus:border-[#E50019]"
                  data-testid="password-input"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-12 bg-[#E50019] hover:bg-[#c00015] text-white font-semibold rounded-xl"
              disabled={loading}
              data-testid="login-button"
            >
              {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-sm mt-6">
          © 2025 PediZone. Tüm hakları saklıdır.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
