import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  MapPin, 
  UserCircle, 
  Package, 
  FileText,
  DollarSign,
  Wallet,
  BarChart3,
  FileStack,
  Calendar,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const Layout = ({ children, user, setUser }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    navigate('/login');
  };

  const menuItems = [
    { icon: LayoutDashboard, label: 'Anasayfa', path: '/dashboard', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: Users, label: 'Kullanıcılar', path: '/users', roles: ['admin', 'regional_manager'] },
    { icon: MapPin, label: 'Bölgeler', path: '/regions', roles: ['admin'] },
    { icon: UserCircle, label: 'Müşteriler', path: '/customers', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: Package, label: 'Ürünler', path: '/products', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: FileText, label: 'Ziyaretler', path: '/visits', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: DollarSign, label: 'Satışlar', path: '/sales', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: Wallet, label: 'Tahsilatlar', path: '/collections', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: BarChart3, label: 'Raporlar', path: '/reports', roles: ['admin', 'regional_manager'] },
    { icon: FileStack, label: 'Dokümanlar', path: '/documents', roles: ['admin', 'regional_manager', 'salesperson'] },
    { icon: Calendar, label: 'Takvim', path: '/calendar', roles: ['admin', 'regional_manager', 'salesperson'] },
  ];

  const filteredMenu = menuItems.filter(item => item.roles.includes(user.role));

  return (
    <div className="min-h-screen bg-white" data-testid="layout-container">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-20 bg-[#E50019] text-white flex items-center justify-between px-4 z-[10000]">
        <div className="flex items-center gap-3">
          <img src="https://customer-assets.emergentagent.com/job_f2a1a2de-506c-4346-999f-22d1252f1d2d/artifacts/oi6kp97t_PediZone.png" alt="PediZone" className="h-12" />
          <span className="text-lg font-bold">PediZone CRM</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-white/10 rounded-lg"
          data-testid="mobile-menu-toggle"
        >
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-[#E50019] text-white z-[99999] transform transition-transform duration-300 lg:translate-x-0 flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="sidebar"
      >
        {/* User Info */}
        <div className="px-6 pb-4 pt-12 border-b border-white/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white text-[#E50019] rounded-full flex items-center justify-center font-bold">
              {user.full_name.charAt(0)}
            </div>
            <div>
              <p className="font-semibold text-sm" data-testid="user-full-name">{user.full_name}</p>
              <p className="text-xs text-white/70" data-testid="user-role">
                {user.role === 'admin' ? 'Yönetici' : user.role === 'regional_manager' ? 'Bölge Sorumlusu' : 'Plasiyer'}
              </p>
            </div>
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 overflow-y-auto px-6 py-6 space-y-1">
          {filteredMenu.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  setSidebarOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                  isActive
                    ? 'bg-white text-[#E50019]'
                    : 'text-white hover:bg-white/10'
                }`}
                data-testid={`menu-${item.path.substring(1)}`}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Logout Button */}
        <div className="p-6 border-t border-white/20">
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start text-white hover:bg-white/10 hover:text-white"
            data-testid="logout-button"
          >
            <LogOut size={20} className="mr-3" />
            Çıkış Yap
          </Button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-[10000] lg:hidden"
          onClick={() => setSidebarOpen(false)}
          data-testid="sidebar-overlay"
        ></div>
      )}

      {/* Main Content */}
      <main className="lg:ml-64 min-h-screen pt-20 lg:pt-0 flex flex-col">
        <div className="p-6 lg:p-8 flex-1" data-testid="main-content">
          {children}
        </div>
        {/* Footer */}
        <footer className="py-4 text-center text-white bg-[#E50019]">
          <p className="text-sm font-medium">PediZone</p>
        </footer>
      </main>
    </div>
  );
};

export default Layout;
