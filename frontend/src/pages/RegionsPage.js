import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Edit, Trash2, MapPin } from 'lucide-react';

const RegionsPage = ({ user, setUser }) => {
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchRegions();
  }, []);

  const fetchRegions = async () => {
    try {
      const response = await axiosInstance.get('/regions');
      setRegions(response.data);
    } catch (error) {
      toast.error('Bölgeler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await axiosInstance.put(`/regions/${editingId}`, formData);
        toast.success('Bölge güncellendi');
      } else {
        await axiosInstance.post('/regions', formData);
        toast.success('Bölge eklendi');
      }
      setDialogOpen(false);
      resetForm();
      fetchRegions();
    } catch (error) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu bölgeyi silmek istediğinize emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/regions/${id}`);
      toast.success('Bölge silindi');
      fetchRegions();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const resetForm = () => {
    setFormData({ name: '', description: '' });
    setEditingId(null);
  };

  const handleEdit = (region) => {
    setFormData({ name: region.name, description: region.description || '' });
    setEditingId(region.id);
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
      <div className="space-y-6" data-testid="regions-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Bölge Yönetimi</h1>
            <p className="text-gray-500 mt-1">Satış bölgelerini yönetin</p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-region-button">
                <Plus size={20} className="mr-2" />
                Yeni Bölge
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md" data-testid="region-dialog">
              <DialogHeader>
                <DialogTitle>{editingId ? 'Bölge Düzenle' : 'Yeni Bölge Ekle'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label>Bölge Adı</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Örn: İstanbul Anadolu"
                    required
                    data-testid="region-name-field"
                  />
                </div>
                <div>
                  <Label>Açıklama</Label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Bölge hakkında kısa bilgi"
                    rows={3}
                    data-testid="region-description-field"
                  />
                </div>
                <div className="flex gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                    İptal
                  </Button>
                  <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-region-button">
                    {editingId ? 'Güncelle' : 'Ekle'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Regions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="regions-grid">
          {regions.map((region) => (
            <div
              key={region.id}
              className="bg-white rounded-xl border border-gray-100 p-6 hover:shadow-lg transition-shadow"
              data-testid={`region-card-${region.name}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                  <MapPin className="text-[#E50019]" size={24} />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleEdit(region)}
                    data-testid={`edit-region-${region.name}`}
                  >
                    <Edit size={16} className="text-gray-600" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(region.id)}
                    data-testid={`delete-region-${region.name}`}
                  >
                    <Trash2 size={16} className="text-red-600" />
                  </Button>
                </div>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{region.name}</h3>
              <p className="text-sm text-gray-600">{region.description || 'Açıklama yok'}</p>
            </div>
          ))}
        </div>

        {regions.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <MapPin size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz bölge yok</h3>
            <p className="text-gray-500">Yeni bir bölge ekleyerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default RegionsPage;
