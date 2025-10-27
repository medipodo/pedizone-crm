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

const SalesPage = ({ user, setUser }) => {
  const [sales, setSales] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    customer_id: '',
    sale_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const [items, setItems] = useState([{ product_id: '', quantity: '', unit_price: '', total: 0 }]);

  useEffect(() => {
    fetchSales();
    fetchCustomers();
    fetchProducts();
    if (user.role !== 'salesperson') {
      fetchUsers();
    }
  }, []);

  const fetchSales = async () => {
    try {
      const response = await axiosInstance.get('/sales');
      setSales(response.data);
    } catch (error) {
      toast.error('Satışlar yüklenemedi');
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

  const fetchProducts = async () => {
    try {
      const response = await axiosInstance.get('/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Ürünler yüklenemedi');
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
    if (items.length === 0 || !items[0].product_id) {
      toast.error('En az bir ürün eklemelisiniz');
      return;
    }

    const totalAmount = items.reduce((sum, item) => sum + item.total, 0);
    const saleData = {
      ...formData,
      items: items.map(item => ({
        product_id: item.product_id,
        product_name: products.find(p => p.id === item.product_id)?.name || '',
        quantity: parseFloat(item.quantity),
        unit_price: parseFloat(item.unit_price),
        total: item.total
      })),
      total_amount: totalAmount
    };

    try {
      await axiosInstance.post('/sales', saleData);
      toast.success('Satış kaydedildi');
      setDialogOpen(false);
      resetForm();
      fetchSales();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (saleId) => {
    if (!window.confirm('Bu satışı silmek istediğinizden emin misiniz?')) return;
    
    try {
      await axiosInstance.delete(`/sales/${saleId}`);
      toast.success('Satış silindi');
      fetchSales();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      sale_date: new Date().toISOString().split('T')[0],
      notes: ''
    });
    setItems([{ product_id: '', quantity: '', unit_price: '', total: 0 }]);
  };

  const addItem = () => {
    setItems([...items, { product_id: '', quantity: '', unit_price: '', total: 0 }]);
  };

  const removeItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  // Adet bazlı fiyat hesaplama
  const calculatePrice = (product, quantity) => {
    const qty = parseFloat(quantity);
    if (!qty || !product) return product?.unit_price || 0;

    // Varyasyon fiyatlarını kontrol et
    if (qty >= 11 && product.price_11_24) {
      return product.price_11_24;
    } else if (qty >= 6 && product.price_6_10) {
      return product.price_6_10;
    } else if (qty >= 1 && product.price_1_5) {
      return product.price_1_5;
    }
    
    return product.unit_price;
  };

  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;

    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        const qty = newItems[index].quantity || 1;
        newItems[index].unit_price = calculatePrice(product, qty);
      }
    }

    if (field === 'quantity') {
      const product = products.find(p => p.id === newItems[index].product_id);
      if (product) {
        newItems[index].unit_price = calculatePrice(product, value);
      }
    }

    if (newItems[index].quantity && newItems[index].unit_price) {
      newItems[index].total = parseFloat(newItems[index].quantity) * parseFloat(newItems[index].unit_price);
    }

    setItems(newItems);
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : '-';
  };

  const getUserName = (userId) => {
    const userItem = users.find(u => u.id === userId);
    return userItem ? userItem.full_name : '-';
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
      <div className="space-y-6" data-testid="sales-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Satış Yönetimi</h1>
            <p className="text-gray-500 mt-1">Satış kayıtlarını yönetin</p>
          </div>
          {(user.role === 'salesperson' || user.role === 'admin') && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-sale-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Satış
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="sale-dialog">
                <DialogHeader>
                  <DialogTitle>Yeni Satış Kaydı</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Müşteri *</Label>
                      <Select value={formData.customer_id} onValueChange={(value) => setFormData({ ...formData, customer_id: value })}>
                        <SelectTrigger data-testid="sale-customer-select">
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
                      <Label>Satış Tarihi *</Label>
                      <Input
                        type="date"
                        value={formData.sale_date}
                        onChange={(e) => setFormData({ ...formData, sale_date: e.target.value })}
                        required
                        data-testid="sale-date-field"
                      />
                    </div>
                  </div>

                  {/* Items */}
                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between mb-4">
                      <Label className="text-base">Ürünler</Label>
                      <Button type="button" size="sm" onClick={addItem} variant="outline" data-testid="add-item-button">
                        <Plus size={16} className="mr-1" /> Ürün Ekle
                      </Button>
                    </div>
                    {items.map((item, index) => (
                      <div key={index} className="grid grid-cols-12 gap-2 mb-3 items-end">
                        <div className="col-span-5">
                          {index === 0 && <Label className="text-xs mb-1">Ürün</Label>}
                          <Select value={item.product_id} onValueChange={(value) => updateItem(index, 'product_id', value)}>
                            <SelectTrigger data-testid={`item-product-select-${index}`}>
                              <SelectValue placeholder="Ürün seçin" />
                            </SelectTrigger>
                            <SelectContent>
                              {products.map((product) => (
                                <SelectItem key={product.id} value={product.id}>{product.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2">
                          {index === 0 && <Label className="text-xs mb-1">Miktar</Label>}
                          <Input
                            type="number"
                            step="0.01"
                            value={item.quantity}
                            onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                            placeholder="0"
                            data-testid={`item-quantity-${index}`}
                          />
                        </div>
                        <div className="col-span-2">
                          {index === 0 && <Label className="text-xs mb-1">Fiyat</Label>}
                          <Input
                            type="number"
                            step="0.01"
                            value={item.unit_price}
                            onChange={(e) => updateItem(index, 'unit_price', e.target.value)}
                            placeholder="0"
                            data-testid={`item-price-${index}`}
                          />
                        </div>
                        <div className="col-span-2">
                          {index === 0 && <Label className="text-xs mb-1">Toplam</Label>}
                          <Input value={item.total.toFixed(2)} readOnly className="bg-gray-50" />
                        </div>
                        <div className="col-span-1">
                          {index === 0 && <div className="h-5"></div>}
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            onClick={() => removeItem(index)}
                            disabled={items.length === 1}
                            data-testid={`remove-item-${index}`}
                          >
                            <Trash2 size={16} className="text-red-600" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    <div className="mt-4 pt-4 border-t">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-lg">Genel Toplam:</span>
                        <span className="text-2xl font-bold text-[#E50019]">
                          {items.reduce((sum, item) => sum + item.total, 0).toFixed(2)} ₺
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <Label>Notlar</Label>
                    <Input
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Satış hakkında notlar"
                      data-testid="sale-notes-field"
                    />
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-sale-button">
                      Kaydet
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Sales Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="sales-table">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Tarih</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Müşteri</th>
                  {user.role !== 'salesperson' && (
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Plasiyer</th>
                  )}
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Ürün Sayısı</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">Toplam</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-gray-50 transition-colors" data-testid={`sale-row-${sale.id}`}>
                    <td className="px-6 py-4 text-sm text-gray-900">{new Date(sale.sale_date).toLocaleDateString('tr-TR')}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{getCustomerName(sale.customer_id)}</td>
                    {user.role !== 'salesperson' && (
                      <td className="px-6 py-4 text-sm text-gray-700">{getUserName(sale.salesperson_id)}</td>
                    )}
                    <td className="px-6 py-4 text-sm text-gray-700">{sale.items.length} ürün</td>
                    <td className="px-6 py-4 text-right text-sm font-semibold text-[#E50019]">
                      {sale.total_amount.toLocaleString('tr-TR')} ₺
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(sale.id)}
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

        {sales.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz satış yok</h3>
            <p className="text-gray-500">Yeni bir satış kaydı ekleyerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SalesPage;
