import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import PageHeader from '@/components/PageHeader';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2, UserCircle } from 'lucide-react';

const CustomersPage = ({ user, setUser }) => {
  const [customers, setCustomers] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
    region_id: '',
    tax_number: '',
    notes: ''
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchCustomers();
    fetchRegions();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axiosInstance.get('/customers');
      setCustomers(response.data);
    } catch (error) {
      toast.error('Müşteriler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await axiosInstance.get('/regions');
      setRegions(response.data);
    } catch (error) {
      console.error('Bölgeler yüklenemedi');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await axiosInstance.put(`/customers/${editingId}`, formData);
        toast.success('Müşteri güncellendi');
      } else {
        await axiosInstance.post('/customers', formData);
        toast.success('Müşteri eklendi');
      }
      setDialogOpen(false);
      resetForm();
      fetchCustomers();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu müşteriyi silmek istediğinize emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/customers/${id}`);
      toast.success('Müşteri silindi');
      fetchCustomers();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      address: '',
      phone: '',
      email: '',
      region_id: '',
      tax_number: '',
      notes: ''
    });
    setEditingId(null);
  };

  const handleEdit = (customer) => {
    setFormData({ ...customer });
    setEditingId(customer.id);
    setDialogOpen(true);
  };

  const getRegionName = (regionId) => {
    const region = regions.find(r => r.id === regionId);
    return region ? region.name : '-';
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
      <div className="space-y-6" data-testid="customers-page">
        <PageHeader 
          title="Müşteri Yönetimi"
          subtitle="Müşteri bilgilerini yönetin"
          action={
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-customer-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Müşteri
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="customer-dialog">
                <DialogHeader>
                  <DialogTitle>{editingId ? 'Müşteri Düzenle' : 'Yeni Müşteri Ekle'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Müşteri Adı *</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        required
                        data-testid="customer-name-field"
                      />
                    </div>
                    <div>
                      <Label>Telefon *</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        required
                        data-testid="customer-phone-field"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>E-posta</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      data-testid="customer-email-field"
                    />
                  </div>
                  <div>
                    <Label>Adres *</Label>
                    <Textarea
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      required
                      rows={2}
                      data-testid="customer-address-field"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Bölge *</Label>
                      <Select value={formData.region_id} onValueChange={(value) => setFormData({ ...formData, region_id: value })}>
                        <SelectTrigger data-testid="customer-region-select">
                          <SelectValue placeholder="Bölge seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          {regions.map((region) => (
                            <SelectItem key={region.id} value={region.id}>{region.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Vergi Numarası</Label>
                      <Input
                        value={formData.tax_number}
                        onChange={(e) => setFormData({ ...formData, tax_number: e.target.value })}
                        data-testid="customer-tax-field"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Notlar</Label>
                    <Textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={2}
                      data-testid="customer-notes-field"
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-customer-button">
                      {editingId ? 'Güncelle' : 'Ekle'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          }
        />

        {/* Customers Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="customers-table">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Müşteri Adı</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Telefon</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Bölge</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Adres</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50 transition-colors" data-testid={`customer-row-${customer.name}`}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{customer.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{customer.phone}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{getRegionName(customer.region_id)}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{customer.address.substring(0, 40)}...</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEdit(customer)}
                        data-testid={`edit-customer-${customer.name}`}
                      >
                        <Edit size={16} className="text-gray-600" />
                      </Button>
                      {user.role === 'admin' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(customer.id)}
                          data-testid={`delete-customer-${customer.name}`}
                        >
                          <Trash2 size={16} className="text-red-600" />
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {customers.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <UserCircle size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz müşteri yok</h3>
            <p className="text-gray-500">Yeni bir müşteri ekleyerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CustomersPage;
