import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import PageHeader from '@/components/PageHeader';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { TrendingUp, Users as UsersIcon, FileText, Wallet, Target, X } from 'lucide-react';
import VisitMap from '@/components/VisitMap';

const Dashboard = ({ user, setUser }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [visits, setVisits] = useState([]);
  const [sales, setSales] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [showPerformanceModal, setShowPerformanceModal] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchMapData();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axiosInstance.get('/dashboard/stats');
      setStats(response.data);
    } catch (error) {
      toast.error('İstatistikler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchMapData = async () => {
    try {
      const [visitsRes, salesRes, customersRes] = await Promise.all([
        axiosInstance.get('/visits'),
        axiosInstance.get('/sales'),
        axiosInstance.get('/customers')
      ]);
      setVisits(visitsRes.data);
      setSales(salesRes.data);
      setCustomers(customersRes.data);
    } catch (error) {
      console.error('Harita verileri yüklenemedi:', error);
    }
  };

  if (loading) {
    return (
      <Layout user={user} setUser={setUser}>
        <div className="flex items-center justify-center h-96">
          <div className="w-12 h-12 border-4 border-[#E50019] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} setUser={setUser}>
      <div className="space-y-6" data-testid="dashboard-page">
        <PageHeader 
          title="Anasayfa"
          subtitle={`Hoş geldiniz, ${user.full_name}`}
          action={
            <div className="text-right">
              <p className="text-sm text-gray-500">Bugün</p>
              <p className="text-lg font-semibold text-gray-900">
                {new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })}
              </p>
            </div>
          }
        />

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {/* Total Sales */}
          {stats && (
            <>
              <div 
                onClick={() => navigate('/sales')}
                className="stat-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm cursor-pointer hover:shadow-lg transition-all hover:border-[#E50019]" 
                data-testid="stat-total-sales"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                    <TrendingUp className="text-[#E50019]" size={24} />
                  </div>
                  <span className="text-2xl font-bold text-gray-900">{stats.total_sales || 0}</span>
                </div>
                <h3 className="text-gray-600 font-medium">Toplam Satış</h3>
                {stats.total_revenue !== undefined && (
                  <p className="text-sm text-gray-500 mt-2">
                    {stats.total_revenue.toLocaleString('tr-TR')} ₺
                  </p>
                )}
              </div>

              {/* Monthly Sales */}
              {stats.monthly_sales_amount !== undefined && (
                <div className="stat-card bg-gradient-to-br from-[#E50019] to-[#c00015] rounded-2xl p-6 text-white shadow-lg" data-testid="stat-monthly-sales">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                      <Target className="text-white" size={24} />
                    </div>
                    {stats.commission_emoji && (
                      <span className="text-4xl">{stats.commission_emoji}</span>
                    )}
                  </div>
                  <h3 className="font-medium">Bu Ay Satış</h3>
                  <p className="text-3xl font-bold mt-2">
                    {stats.monthly_sales_amount.toLocaleString('tr-TR')} ₺
                  </p>
                </div>
              )}

              {/* Total Visits */}
              <div 
                onClick={() => navigate('/visits')}
                className="stat-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm cursor-pointer hover:shadow-lg transition-all hover:border-[#E50019]" 
                data-testid="stat-total-visits"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                    <FileText className="text-[#E50019]" size={24} />
                  </div>
                  <span className="text-2xl font-bold text-gray-900">{stats.total_visits || 0}</span>
                </div>
                <h3 className="text-gray-600 font-medium">Toplam Ziyaret</h3>
              </div>

              {/* Total Collections */}
              {stats.total_collections !== undefined && (
                <div className="stat-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm" data-testid="stat-total-collections">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                      <Wallet className="text-[#E50019]" size={24} />
                    </div>
                  </div>
                  <h3 className="text-gray-600 font-medium">Tahsilat</h3>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    {stats.total_collections.toLocaleString('tr-TR')} ₺
                  </p>
                </div>
              )}

              {/* Team Size (for regional manager) */}
              {stats.team_size !== undefined && (
                <div className="stat-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm" data-testid="stat-team-size">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                      <UsersIcon className="text-[#E50019]" size={24} />
                    </div>
                    <span className="text-2xl font-bold text-gray-900">{stats.team_size}</span>
                  </div>
                  <h3 className="text-gray-600 font-medium">Ekip Büyüklüğü</h3>
                </div>
              )}

              {/* Total Customers (for admin) */}
              {stats.total_customers !== undefined && (
                <div 
                  onClick={() => navigate('/customers')}
                  className="stat-card bg-white rounded-2xl p-6 border border-gray-100 shadow-sm cursor-pointer hover:shadow-lg transition-all hover:border-[#E50019]" 
                  data-testid="stat-total-customers"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                      <UsersIcon className="text-[#E50019]" size={24} />
                    </div>
                    <span className="text-2xl font-bold text-gray-900">{stats.total_customers}</span>
                  </div>
                  <h3 className="text-gray-600 font-medium">Toplam Müşteri</h3>
                </div>
              )}
            </>
          )}
        </div>

        {/* Performance Info - Now Clickable */}
        {stats && (
          <div 
            onClick={() => setShowPerformanceModal(true)}
            className="bg-gradient-to-r from-white to-red-50 rounded-2xl p-8 border border-gray-100 cursor-pointer hover:shadow-lg transition-all" 
            data-testid="performance-info"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {user.role === 'salesperson' ? 'Prim Durumu' : 'Performans Göstergeleri'} 👆 Tıklayın
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-white rounded-xl border border-gray-100">
                <div className="text-3xl mb-2">🌱</div>
                <p className="text-sm text-gray-600 font-medium">Başlangıç</p>
                <p className="text-xs text-gray-500 mt-1">0-10,000₺</p>
              </div>
              <div className="text-center p-4 bg-white rounded-xl border border-gray-100">
                <div className="text-3xl mb-2">💪</div>
                <p className="text-sm text-gray-600 font-medium">Güçlü</p>
                <p className="text-xs text-gray-500 mt-1">10,001-30,000₺</p>
              </div>
              <div className="text-center p-4 bg-white rounded-xl border border-gray-100">
                <div className="text-3xl mb-2">🔥</div>
                <p className="text-sm text-gray-600 font-medium">Lider</p>
                <p className="text-xs text-gray-500 mt-1">30,001-50,000₺</p>
              </div>
              <div className="text-center p-4 bg-white rounded-xl border border-gray-100">
                <div className="text-3xl mb-2">🏆</div>
                <p className="text-sm text-gray-600 font-medium">Şampiyon</p>
                <p className="text-xs text-gray-500 mt-1">50,001₺+</p>
              </div>
            </div>
            {user.role === 'salesperson' && stats.monthly_sales_amount !== undefined && (
              <div className="mt-6 p-4 bg-white rounded-xl border-2 border-[#E50019]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Bu Ay Pirime Esas Satış</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {stats.monthly_sales_amount.toLocaleString('tr-TR')} ₺
                    </p>
                  </div>
                  <div className="text-6xl">
                    {stats.commission_emoji || '🌱'}
                  </div>
                </div>
              </div>
            )}
            {user.role !== 'salesperson' && stats.monthly_sales_amount !== undefined && (
              <div className="mt-6 p-4 bg-white rounded-xl border border-gray-100">
                <p className="text-sm text-gray-600">
                  {user.role === 'admin' ? 'Toplam Sistem Performansı' : 'Ekip Performansı'}
                </p>
                <p className="text-2xl font-bold text-[#E50019] mt-1">
                  Bu Ay: {stats.monthly_sales_amount.toLocaleString('tr-TR')} ₺
                </p>
              </div>
            )}
          </div>
        )}

        {/* Performance Modal */}
        {showPerformanceModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowPerformanceModal(false)}>
            <div className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Performans Sistemi Hakkında</h2>
                <button onClick={() => setShowPerformanceModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X size={24} />
                </button>
              </div>
              
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-red-50 to-white p-6 rounded-xl">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Son 1 Ay İstatistikleri</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-gray-100">
                      <p className="text-sm text-gray-600">Toplam Satış</p>
                      <p className="text-2xl font-bold text-[#E50019]">{stats?.total_sales || 0}</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-100">
                      <p className="text-sm text-gray-600">Toplam Ziyaret</p>
                      <p className="text-2xl font-bold text-[#E50019]">{stats?.total_visits || 0}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-4">🎯 Motivasyon & Hedefler</h3>
                  <div className="space-y-3 text-gray-700">
                    <p className="flex items-start gap-2">
                      <span className="text-lg">✨</span>
                      <span><strong>Sürekli İyileştirme:</strong> Her gün önceki günden daha iyisin! Sistemimiz performansınızı takip ediyor.</span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-lg">🎁</span>
                      <span><strong>Ödül Sistemi:</strong> Başarılı satışlarınız için prim kazanıyorsunuz. Ne kadar çok satarsanız, o kadar çok kazanırsınız!</span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-lg">📈</span>
                      <span><strong>Seviye Atlama:</strong> Başlangıç → Güçlü → Lider → Şampiyon! Hangi seviyedesiniz?</span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-lg">🏆</span>
                      <span><strong>Takım Ruhu:</strong> Bireysel başarınız, takımın başarısıdır. Beraber büyüyoruz!</span>
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-[#E50019] to-[#c00015] text-white p-6 rounded-xl">
                  <h3 className="text-lg font-bold mb-2">💪 Bu Ay Hedefiniz</h3>
                  <p className="text-3xl font-bold mb-2">
                    {stats?.monthly_sales_amount?.toLocaleString('tr-TR') || '0'} ₺
                  </p>
                  <p className="text-sm opacity-90">Harikasınız! Devam edin! 🚀</p>
                </div>

                <div className="text-center">
                  <p className="text-sm text-gray-500 italic">
                    "Başarı, küçük çabaların günlük tekrarıdır." - Robert Collier
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Visit Map */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Ziyaret Haritası</h2>
          <VisitMap visits={visits} sales={sales} customers={customers} />
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
