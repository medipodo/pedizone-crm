import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Trash2 } from 'lucide-react';

const CollectionsPage = ({ user, setUser }) => {
  const [collections, setCollections] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    customer_id: '',
    amount: '',
    collection_date: new Date().toISOString().split('T')[0],
    payment_method: 'nakit',
    notes: ''
  });

  useEffect(() => {
    fetchCollections();
    fetchCustomers();
    if (user.role !== 'salesperson') {
      fetchUsers();
    }
  }, []);

  const fetchCollections = async () => {
    try {
      const response = await axiosInstance.get('/collections');
      setCollections(response.data);
    } catch (error) {
      toast.error('Tahsilatlar yüklenemedi');
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
      const data = { ...formData, amount: parseFloat(formData.amount) };
      await axiosInstance.post('/collections', data);
      toast.success('Tahsilat kaydedildi');
      setDialogOpen(false);
      resetForm();
      fetchCollections();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (collectionId) => {
    if (!window.confirm('Bu tahsilatı silmek istediğinizden emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/collections/${collectionId}`);
      toast.success('Tahsilat silindi');
      fetchCollections();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      amount: '',
      collection_date: new Date().toISOString().split('T')[0],
      payment_method: 'nakit',
      notes: ''
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

  const getPaymentMethodLabel = (method) => {
    const labels = {
      nakit: 'Nakit',
      kredi_karti: 'Kredi Kartı',
      banka_transferi: 'Banka Transferi'
    };
    return labels[method] || method;
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
      <div className="space-y-6" data-testid="collections-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tahsilat Yönetimi</h1>
            <p className="text-gray-500 mt-1">Tahsilat kayıtlarını yönetin</p>
          </div>
          {(user.role === 'salesperson' || user.role === 'admin') && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-collection-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Tahsilat
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md" data-testid="collection-dialog">
                <DialogHeader>
                  <DialogTitle>Yeni Tahsilat Kaydı</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label>Müşteri *</Label>
                    <Select value={formData.customer_id} onValueChange={(value) => setFormData({ ...formData, customer_id: value })}>
                      <SelectTrigger data-testid="collection-customer-select">
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
                    <Label>Tutar (₺) *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      required
                      data-testid="collection-amount-field"
                    />
                  </div>
                  <div>
                    <Label>Tahsilat Tarihi *</Label>
                    <Input
                      type="date"
                      value={formData.collection_date}
                      onChange={(e) => setFormData({ ...formData, collection_date: e.target.value })}
                      required
                      data-testid="collection-date-field"
                    />
                  </div>
                  <div>
                    <Label>Ödeme Yöntemi *</Label>
                    <Select value={formData.payment_method} onValueChange={(value) => setFormData({ ...formData, payment_method: value })}>
                      <SelectTrigger data-testid="collection-payment-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="nakit">Nakit</SelectItem>
                        <SelectItem value="kredi_karti">Kredi Kartı</SelectItem>
                        <SelectItem value="banka_transferi">Banka Transferi</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Notlar</Label>
                    <Input
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Tahsilat hakkında notlar"
                      data-testid="collection-notes-field"
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-collection-button">
                      Kaydet
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Collections Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="collections-table">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Müşteri</th>
                  {user.role !== 'salesperson' && (
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Plasiyer</th>
                  )}
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Ödeme Yöntemi</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">Tutar</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {collections.map((collection) => (
                  <tr key={collection.id} className="hover:bg-gray-50 transition-colors" data-testid={`collection-row-${collection.id}`}>
                    <td className="px-6 py-4 text-sm text-gray-900">{new Date(collection.collection_date).toLocaleDateString('tr-TR')}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{getCustomerName(collection.customer_id)}</td>
                    {user.role !== 'salesperson' && (
                      <td className="px-6 py-4 text-sm text-gray-700">{getUserName(collection.salesperson_id)}</td>
                    )}
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <span className="inline-flex px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
                        {getPaymentMethodLabel(collection.payment_method)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-semibold text-green-600">
                      {collection.amount.toLocaleString('tr-TR')} ₺
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(collection.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 size={16} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {collections.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz tahsilat yok</h3>
            <p className="text-gray-500">Yeni bir tahsilat kaydı ekleyerek başlayın</p>
          </div>
        )}

        {/* Total Collections */}
        {collections.length > 0 && (
          <div className="bg-gradient-to-r from-green-50 to-white rounded-xl p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Toplam Tahsilat</h3>
              <span className="text-3xl font-bold text-green-600">
                {collections.reduce((sum, c) => sum + c.amount, 0).toLocaleString('tr-TR')} ₺
              </span>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CollectionsPage;
