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
import { Plus, Edit, Trash2, Package, Camera } from 'lucide-react';

const ProductsPage = ({ user, setUser }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    unit_price: '',
    price_1_5: '',
    price_6_10: '',
    price_11_24: '',
    unit: 'adet',
    photo_base64: ''
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axiosInstance.get('/products');
      setProducts(response.data);
    } catch (error) {
      toast.error('Ürünler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = { 
        ...formData, 
        unit_price: parseFloat(formData.unit_price),
        price_1_5: formData.price_1_5 ? parseFloat(formData.price_1_5) : null,
        price_6_10: formData.price_6_10 ? parseFloat(formData.price_6_10) : null,
        price_11_24: formData.price_11_24 ? parseFloat(formData.price_11_24) : null
      };
      if (editingId) {
        await axiosInstance.put(`/products/${editingId}`, data);
        toast.success('Ürün güncellendi');
      } else {
        await axiosInstance.post('/products', data);
        toast.success('Ürün eklendi');
      }
      setDialogOpen(false);
      resetForm();
      fetchProducts();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu ürünü devre dışı bırakmak istediğinize emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/products/${id}`);
      toast.success('Ürün devre dışı bırakıldı');
      fetchProducts();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      description: '',
      unit_price: '',
      price_1_5: '',
      price_6_10: '',
      price_11_24: '',
      unit: 'adet',
      photo_base64: ''
    });
    setEditingId(null);
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

  const handleEdit = (product) => {
    setFormData({ 
      ...product, 
      unit_price: product.unit_price.toString(),
      price_1_5: product.price_1_5 ? product.price_1_5.toString() : '',
      price_6_10: product.price_6_10 ? product.price_6_10.toString() : '',
      price_11_24: product.price_11_24 ? product.price_11_24.toString() : '',
      photo_base64: product.photo_base64 || ''
    });
    setEditingId(product.id);
    setDialogOpen(true);
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
      <div className="space-y-6" data-testid="products-page">
        <PageHeader 
          title="Ürün Yönetimi"
          subtitle="Ürün kataloğunu yönetin"
          action={user.role === 'admin' && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-product-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Ürün
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="product-dialog">
                <DialogHeader>
                  <DialogTitle>{editingId ? 'Ürün Düzenle' : 'Yeni Ürün Ekle'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Ürün Kodu *</Label>
                      <Input
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        placeholder="Örn: PRD001"
                        required
                        data-testid="product-code-field"
                      />
                    </div>
                    <div>
                      <Label>Ürün Adı *</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        required
                        data-testid="product-name-field"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Açıklama</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={2}
                      data-testid="product-description-field"
                    />
                  </div>
                  
                  {/* Fotoğraf Upload */}
                  <div>
                    <Label>Ürün Fotoğrafı</Label>
                    <div className="mt-2">
                      <label className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-[#E50019] transition-colors">
                        <div className="text-center">
                          <Package className="mx-auto text-gray-400 mb-2" size={32} />
                          <p className="text-sm text-gray-500">Fotoğraf yükle (Maks 5MB)</p>
                        </div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handlePhotoUpload}
                          className="hidden"
                          data-testid="product-photo-input"
                        />
                      </label>
                      {formData.photo_base64 && (
                        <img src={formData.photo_base64} alt="Preview" className="mt-2 w-full h-32 object-cover rounded-lg" />
                      )}
                    </div>
                  </div>

                  <div>
                    <Label>Birim *</Label>
                    <Input
                      value={formData.unit}
                      onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                      placeholder="adet, kg, litre"
                      required
                      data-testid="product-unit-field"
                    />
                  </div>

                  {/* Fiyat Varyasyonları */}
                  <div className="border-t pt-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Fiyat Varyasyonları</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>1-5 Adet Fiyatı (₺) *</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.price_1_5}
                          onChange={(e) => setFormData({ ...formData, price_1_5: e.target.value })}
                          placeholder="Örn: 2500"
                          data-testid="product-price-1-5-field"
                        />
                      </div>
                      <div>
                        <Label>6-10 Adet Fiyatı (₺)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.price_6_10}
                          onChange={(e) => setFormData({ ...formData, price_6_10: e.target.value })}
                          placeholder="Örn: 2300"
                          data-testid="product-price-6-10-field"
                        />
                      </div>
                      <div>
                        <Label>11-24 Adet Fiyatı (₺)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.price_11_24}
                          onChange={(e) => setFormData({ ...formData, price_11_24: e.target.value })}
                          placeholder="Örn: 2000"
                          data-testid="product-price-11-24-field"
                        />
                      </div>
                      <div>
                        <Label>Varsayılan Fiyat (₺) *</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.unit_price}
                          onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                          required
                          placeholder="Örn: 2500"
                          data-testid="product-price-field"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">* Adet bazlı fiyatlandırma için varyasyonları doldurun</p>
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-product-button">
                      {editingId ? 'Güncelle' : 'Ekle'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        />

        {/* Products Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="products-grid">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow"
              data-testid={`product-card-${product.code}`}
            >
              {/* Product Image */}
              <div className="relative h-32 bg-gray-100">
                {product.photo_base64 ? (
                  <img 
                    src={product.photo_base64} 
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-red-50">
                    <Package className="text-[#E50019]" size={40} />
                  </div>
                )}
                {user.role === 'admin' && (
                  <div className="absolute top-2 right-2 flex gap-1">
                    <Button
                      size="sm"
                      className="bg-white/90 hover:bg-white h-7 w-7 p-0"
                      onClick={() => handleEdit(product)}
                      data-testid={`edit-product-${product.code}`}
                    >
                      <Edit size={14} className="text-gray-600" />
                    </Button>
                    <Button
                      size="sm"
                      className="bg-white/90 hover:bg-white h-7 w-7 p-0"
                      onClick={() => handleDelete(product.id)}
                      data-testid={`delete-product-${product.code}`}
                    >
                      <Trash2 size={14} className="text-red-600" />
                    </Button>
                  </div>
                )}
              </div>
              
              {/* Product Info */}
              <div className="p-6">
                <div className="mb-2">
                  <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                    {product.code}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{product.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{product.description || 'Açıklama yok'}</p>
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <span className="text-sm text-gray-500">{product.unit}</span>
                  <span className="text-xl font-bold text-[#E50019]">
                    {product.unit_price.toLocaleString('tr-TR')} ₺
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {products.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <Package size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz ürün yok</h3>
            <p className="text-gray-500">Yeni bir ürün ekleyerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ProductsPage;
