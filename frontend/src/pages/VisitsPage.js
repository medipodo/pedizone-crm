import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Eye, Camera } from 'lucide-react';

const VisitsPage = ({ user, setUser }) => {
  const [visits, setVisits] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [filterCustomer, setFilterCustomer] = useState('');
  const [formData, setFormData] = useState({
    customer_id: '',
    visit_date: new Date().toISOString().split('T')[0],
    notes: '',
    latitude: '',
    longitude: '',
    photo_base64: '',
    status: 'gorusuldu'
  });

  useEffect(() => {
    fetchVisits();
    fetchCustomers();
    if (user.role !== 'salesperson') {
      fetchUsers();
    }
  }, []);

  const fetchVisits = async () => {
    try {
      const response = await axiosInstance.get('/visits');
      setVisits(response.data);
    } catch (error) {
      toast.error('Ziyaretler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axiosInstance.get('/customers');
      setCustomers(response.data);
    } catch (error) {
      console.error('Müşteriler yüklenemedi');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axiosInstance.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        customer_id: formData.customer_id,
        salesperson_id: user.id,
        visit_date: new Date(formData.visit_date).toISOString(),
        notes: formData.notes || '',
        location: (formData.latitude && formData.longitude) ? {
          latitude: parseFloat(formData.latitude),
          longitude: parseFloat(formData.longitude)
        } : null
      };
      await axiosInstance.post('/visits', data);
      toast.success('Ziyaret kaydedildi');
      setDialogOpen(false);
      resetForm();
      fetchVisits();
    } catch (error) {
      console.error('Ziyaret ekleme hatası:', error);
      toast.error(error.response?.data?.detail || 'İşlem başarısız');
    }
  };

  const handleDelete = async (visitId) => {
    if (!window.confirm('Bu ziyareti silmek istediğinizden emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/visits/${visitId}`);
      toast.success('Ziyaret silindi');
      fetchVisits();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Fotoğraf boyutu 5MB\'dan küçük olmalı');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, photo_base64: reader.result });
      };
      reader.readAsDataURL(file);
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      visit_date: new Date().toISOString().split('T')[0],
      notes: '',
      latitude: '',
      longitude: '',
      photo_base64: '',
      status: 'gorusuldu'
    });
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : '-';
  };

  const getUserName = (userId) => {
    const userItem = users.find(u => u.id === userId);
    return userItem ? userItem.full_name : '-';
  };

  const handleViewVisit = async (visitId) => {
    try {
      const response = await axiosInstance.get(`/visits/${visitId}`);
      setSelectedVisit(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Ziyaret detayı yüklenemedi');
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
      <div className="space-y-6" data-testid="visits-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Ziyaret Yönetimi</h1>
            <p className="text-gray-500 mt-1">Müşteri ziyaretlerini takip edin</p>
          </div>
          {(user.role === 'salesperson' || user.role === 'admin') && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-visit-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Ziyaret
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto" data-testid="visit-dialog">
                <DialogHeader>
                  <DialogTitle>Yeni Ziyaret Kaydı</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label>Müşteri *</Label>
                    <Select value={formData.customer_id} onValueChange={(value) => setFormData({ ...formData, customer_id: value })}>
                      <SelectTrigger data-testid="visit-customer-select">
                        <SelectValue placeholder="Müşteri seçin" />
                      </SelectTrigger>
                      <SelectContent>
                        {customers.map((customer) => (
                          <SelectItem key={customer.id} value={customer.id}>{customer.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Ziyaret Tarihi *</Label>
                    <Input
                      type="date"
                      value={formData.visit_date}
                      onChange={(e) => setFormData({ ...formData, visit_date: e.target.value })}
                      required
                      data-testid="visit-date-field"
                    />
                  </div>
                  <div>
                    <Label>Ziyaret Durumu *</Label>
                    <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                      <SelectTrigger data-testid="visit-status-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gorusuldu">
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-green-500"></span>
                            <span>Görüşüldü</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="randevu_alindi">
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                            <span>Randevu Alındı</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="anlasildi">
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-[#E50019]"></span>
                            <span>Anlaşıldı</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Notlar</Label>
                    <Textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Ziyaret hakkında notlarınız"
                      rows={3}
                      data-testid="visit-notes-field"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Enlem (Latitude)</Label>
                      <Input
                        type="number"
                        step="any"
                        value={formData.latitude}
                        onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                        placeholder="Örn: 41.0082"
                        data-testid="visit-latitude-field"
                      />
                    </div>
                    <div>
                      <Label>Boylam (Longitude)</Label>
                      <Input
                        type="number"
                        step="any"
                        value={formData.longitude}
                        onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                        placeholder="Örn: 28.9784"
                        data-testid="visit-longitude-field"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Fotoğraf</Label>
                    <div className="mt-2">
                      <label className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-[#E50019] transition-colors">
                        <div className="text-center">
                          <Camera className="mx-auto text-gray-400 mb-2" size={32} />
                          <p className="text-sm text-gray-500">Fotoğraf yükle (Maks 5MB)</p>
                        </div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handlePhotoUpload}
                          className="hidden"
                          data-testid="visit-photo-input"
                        />
                      </label>
                      {formData.photo_base64 && (
                        <img src={formData.photo_base64} alt="Preview" className="mt-2 w-full h-32 object-cover rounded-lg" />
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-visit-button">
                      Kaydet
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Filtreler</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label className="text-sm">Başlangıç Tarihi</Label>
              <Input
                type="date"
                value={filterStartDate}
                onChange={(e) => setFilterStartDate(e.target.value)}
                data-testid="filter-start-date"
              />
            </div>
            <div>
              <Label className="text-sm">Bitiş Tarihi</Label>
              <Input
                type="date"
                value={filterEndDate}
                onChange={(e) => setFilterEndDate(e.target.value)}
                data-testid="filter-end-date"
              />
            </div>
            <div>
              <Label className="text-sm">Müşteri</Label>
              <Select value={filterCustomer} onValueChange={setFilterCustomer}>
                <SelectTrigger data-testid="filter-customer">
                  <SelectValue placeholder="Tüm müşteriler" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tüm müşteriler</SelectItem>
                  {customers.map((customer) => (
                    <SelectItem key={customer.id} value={customer.id}>{customer.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button
              onClick={() => {
                setFilterStartDate('');
                setFilterEndDate('');
                setFilterCustomer('');
              }}
              variant="outline"
              size="sm"
            >
              Filtreleri Temizle
            </Button>
          </div>
        </div>

        {/* Visits Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="visits-table">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Müşteri</th>
                  {user.role !== 'salesperson' && (
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Plasiyer</th>
                  )}
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Notlar</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Fotoğraf</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {visits
                  .filter(visit => {
                    if (filterStartDate && visit.visit_date < filterStartDate) return false;
                    if (filterEndDate && visit.visit_date > filterEndDate) return false;
                    if (filterCustomer && filterCustomer !== 'all' && visit.customer_id !== filterCustomer) return false;
                    return true;
                  })
                  .map((visit) => (
                  <tr key={visit.id} className="hover:bg-gray-50 transition-colors" data-testid={`visit-row-${visit.id}`}>
                    <td className="px-6 py-4 text-sm text-gray-900">{new Date(visit.visit_date).toLocaleDateString('tr-TR')}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{getCustomerName(visit.customer_id)}</td>
                    {user.role !== 'salesperson' && (
                      <td className="px-6 py-4 text-sm text-gray-700">{getUserName(visit.salesperson_id)}</td>
                    )}
                    <td className="px-6 py-4 text-sm text-gray-700">{visit.notes ? visit.notes.substring(0, 50) : '-'}</td>
                    <td className="px-6 py-4 text-center">
                      {visit.photo_base64 ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-50 text-green-700">
                          <Camera size={12} className="mr-1" /> Var
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">Yok</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleViewVisit(visit.id)}
                        data-testid={`view-visit-${visit.id}`}
                      >
                        <Eye size={16} className="text-gray-600" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {visits.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz ziyaret yok</h3>
            <p className="text-gray-500">Yeni bir ziyaret kaydı ekleyerek başlayın</p>
          </div>
        )}
      </div>

      {/* View Visit Dialog */}
      {selectedVisit && (
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="max-w-2xl" data-testid="view-visit-dialog">
            <DialogHeader>
              <DialogTitle>Ziyaret Detayı</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Müşteri</p>
                  <p className="font-semibold">{getCustomerName(selectedVisit.customer_id)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tarih</p>
                  <p className="font-semibold">{new Date(selectedVisit.visit_date).toLocaleDateString('tr-TR')}</p>
                </div>
              </div>
              {selectedVisit.notes && (
                <div>
                  <p className="text-sm text-gray-500">Notlar</p>
                  <p className="text-gray-900">{selectedVisit.notes}</p>
                </div>
              )}
              {(selectedVisit.latitude || selectedVisit.longitude) && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Konum</p>
                  <p className="text-gray-900">Enlem: {selectedVisit.latitude}, Boylam: {selectedVisit.longitude}</p>
                </div>
              )}
              {selectedVisit.photo_base64 && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Fotoğraf</p>
                  <img src={selectedVisit.photo_base64} alt="Ziyaret" className="w-full rounded-lg" />
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Layout>
  );
};

export default VisitsPage;
