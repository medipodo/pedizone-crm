import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BarChart3, FileText, TrendingUp, Download } from 'lucide-react';

const ReportsPage = ({ user, setUser }) => {
  const [reportType, setReportType] = useState('sales');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [regions, setRegions] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [selectedSalesperson, setSelectedSalesperson] = useState('all');
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchRegions();
    fetchUsers();
    fetchProducts();
  }, []);

  const fetchRegions = async () => {
    try {
      const response = await axiosInstance.get('/regions');
      setRegions(response.data);
    } catch (error) {
      console.error('Bölgeler yüklenemedi');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axiosInstance.get('/users');
      setUsers(response.data.filter(u => u.role === 'salesperson'));
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi');
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axiosInstance.get('/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Ürünler yüklenemedi');
    }
  };

  const generateReport = async () => {
    if (!startDate || !endDate) {
      toast.error('Başlangıç ve bitiş tarihi seçin');
      return;
    }

    setLoading(true);
    try {
      const endpoint = reportType === 'sales' ? '/reports/sales' : '/reports/visits';
      const response = await axiosInstance.get(endpoint, {
        params: { start_date: startDate, end_date: endDate }
      });
      
      let filteredData = response.data;
      
      // Apply filters
      if (reportType === 'sales' && filteredData.sales) {
        let filtered = filteredData.sales;
        if (selectedRegion !== 'all') {
          // Filter by region - would need salesperson region info
          const regionSalespeople = users.filter(u => u.region_id === selectedRegion).map(u => u.id);
          filtered = filtered.filter(s => regionSalespeople.includes(s.salesperson_id));
        }
        if (selectedSalesperson !== 'all') {
          filtered = filtered.filter(s => s.salesperson_id === selectedSalesperson);
        }
        filteredData = { ...filteredData, sales: filtered, total_count: filtered.length, total_amount: filtered.reduce((sum, s) => sum + s.total_amount, 0) };
      }
      
      setReportData(filteredData);
      toast.success('Rapor oluşturuldu');
    } catch (error) {
      toast.error('Rapor oluşturulamadı');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!reportData) return;
    
    let csvContent = '';
    if (reportType === 'sales') {
      csvContent = 'Tarih,Müşteri ID,Tutar\n';
      reportData.sales.forEach(sale => {
        csvContent += `${sale.sale_date},${sale.customer_id},${sale.total_amount}\n`;
      });
    } else {
      csvContent = 'Tarih,Müşteri ID,Notlar\n';
      reportData.visits.forEach(visit => {
        csvContent += `${visit.visit_date},${visit.customer_id},"${visit.notes || ''}"\n`;
      });
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${reportType}_rapor_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    toast.success('Rapor indirildi');
  };

  return (
    <Layout user={user} setUser={setUser}>
      <div className="space-y-6" data-testid="reports-page">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Raporlar</h1>
          <p className="text-gray-500 mt-1">Detaylı raporlar oluşturun</p>
        </div>

        {/* Report Filters */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Rapor Parametreleri</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <Label>Rapor Tipi</Label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger data-testid="report-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">Satış Raporu</SelectItem>
                  <SelectItem value="visits">Ziyaret Raporu</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Başlangıç Tarihi</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                data-testid="report-start-date"
              />
            </div>
            <div>
              <Label>Bitiş Tarihi</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                data-testid="report-end-date"
              />
            </div>
          </div>
          
          {reportType === 'sales' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <Label>Bölge</Label>
                <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tüm Bölgeler</SelectItem>
                    {regions.map(region => (
                      <SelectItem key={region.id} value={region.id}>{region.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Plasiyer</Label>
                <Select value={selectedSalesperson} onValueChange={setSelectedSalesperson}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tüm Plasiyerler</SelectItem>
                    {users.map(userItem => (
                      <SelectItem key={userItem.id} value={userItem.id}>{userItem.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              onClick={generateReport}
              className="bg-[#E50019] hover:bg-[#c00015] text-white"
              disabled={loading}
              data-testid="generate-report-button"
            >
              {loading ? 'Oluşturuluyor...' : 'Rapor Oluştur'}
            </Button>
            {reportData && (
              <Button
                onClick={exportToCSV}
                variant="outline"
                className="border-[#E50019] text-[#E50019]"
              >
                <Download size={16} className="mr-2" />
                CSV İndir
              </Button>
            )}
          </div>
        </div>

        {/* Report Results */}
        {reportData && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {reportType === 'sales' ? (
                <>
                  <div className="bg-gradient-to-br from-[#E50019] to-[#c00015] rounded-xl p-6 text-white">
                    <div className="flex items-center justify-between mb-4">
                      <TrendingUp size={32} />
                      <span className="text-4xl font-bold">{reportData.total_count}</span>
                    </div>
                    <h3 className="font-semibold">Toplam Satış</h3>
                  </div>
                  <div className="bg-white rounded-xl p-6 border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                        <BarChart3 className="text-[#E50019]" size={24} />
                      </div>
                    </div>
                    <h3 className="text-gray-600 font-medium mb-2">Toplam Ciro</h3>
                    <p className="text-2xl font-bold text-gray-900">
                      {reportData.total_amount?.toLocaleString('tr-TR')} ₺
                    </p>
                  </div>
                  <div className="bg-white rounded-xl p-6 border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                        <FileText className="text-[#E50019]" size={24} />
                      </div>
                    </div>
                    <h3 className="text-gray-600 font-medium mb-2">Ortalama Satış</h3>
                    <p className="text-2xl font-bold text-gray-900">
                      {reportData.total_count > 0
                        ? (reportData.total_amount / reportData.total_count).toFixed(2)
                        : '0.00'} ₺
                    </p>
                  </div>
                </>
              ) : (
                <div className="bg-gradient-to-br from-[#E50019] to-[#c00015] rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <FileText size={32} />
                    <span className="text-4xl font-bold">{reportData.total_count}</span>
                  </div>
                  <h3 className="font-semibold">Toplam Ziyaret</h3>
                </div>
              )}
            </div>

            {/* Data Table */}
            <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">
                  {reportType === 'sales' ? 'Satış Detayları' : 'Ziyaret Detayları'}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Tarih</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Müşteri ID</th>
                      {reportType === 'sales' && (
                        <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Tutar</th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {(reportType === 'sales' ? reportData.sales : reportData.visits)?.slice(0, 20).map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {new Date(reportType === 'sales' ? item.sale_date : item.visit_date).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-700">{item.customer_id.substring(0, 8)}...</td>
                        {reportType === 'sales' && (
                          <td className="px-6 py-4 text-sm text-right font-semibold text-[#E50019]">
                            {item.total_amount?.toLocaleString('tr-TR')} ₺
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Top Products */}
        {reportData && reportType === 'sales' && reportData.sales && (
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">En Çok Satılan Ürünler</h3>
            <div className="space-y-3">
              {(() => {
                const productSales = {};
                reportData.sales.forEach(sale => {
                  sale.items.forEach(item => {
                    if (!productSales[item.product_id]) {
                      productSales[item.product_id] = { name: item.product_name, quantity: 0, total: 0 };
                    }
                    productSales[item.product_id].quantity += item.quantity;
                    productSales[item.product_id].total += item.total;
                  });
                });
                
                return Object.entries(productSales)
                  .sort((a, b) => b[1].total - a[1].total)
                  .slice(0, 5)
                  .map(([productId, data], index) => (
                    <div key={productId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 bg-[#E50019] text-white rounded-full flex items-center justify-center font-bold">
                          {index + 1}
                        </span>
                        <div>
                          <p className="font-semibold text-gray-900">{data.name}</p>
                          <p className="text-sm text-gray-600">{data.quantity} adet</p>
                        </div>
                      </div>
                      <span className="text-lg font-bold text-[#E50019]">
                        {data.total.toLocaleString('tr-TR')} ₺
                      </span>
                    </div>
                  ));
              })()}
            </div>
          </div>
        )}

        {!reportData && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <BarChart3 size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Rapor oluşturmak için parametreleri seçin</h3>
            <p className="text-gray-500">Tarih aralığı ve rapor tipini seçerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ReportsPage;
