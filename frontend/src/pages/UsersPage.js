import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import PageHeader from '@/components/PageHeader';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2 } from 'lucide-react';

const UsersPage = ({ user, setUser }) => {
  const [users, setUsers] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'salesperson',
    region_id: ''
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchRegions();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axiosInstance.get('/users');
      setUsers(response.data);
    } catch (error) {
      toast.error('Kullanıcılar yüklenemedi');
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
        await axiosInstance.put(`/users/${editingId}`, formData);
        toast.success('Kullanıcı güncellendi');
      } else {
        await axiosInstance.post('/users', formData);
        toast.success('Kullanıcı eklendi');
      }
      setDialogOpen(false);
      resetForm();
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'İşlem başarısız');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu kullanıcıyı silmek istediğinize emin misiniz?')) return;
    try {
      await axiosInstance.delete(`/users/${id}`);
      toast.success('Kullanıcı silindi');
      fetchUsers();
    } catch (error) {
      toast.error('Silme işlemi başarısız');
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      full_name: '',
      password: '',
      role: 'salesperson',
      region_id: ''
    });
    setEditingId(null);
  };

  const handleEdit = (userItem) => {
    setFormData({
      username: userItem.username,
      email: userItem.email,
      full_name: userItem.full_name,
      password: '',
      role: userItem.role,
      region_id: userItem.region_id || ''
    });
    setEditingId(userItem.id);
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
      <div className="space-y-6" data-testid="users-page">
        <PageHeader 
          title="Kullanıcı Yönetimi"
          subtitle="Sistem kullanıcılarını yönetin"
          action={user.role === 'admin' && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-user-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Kullanıcı
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md" data-testid="user-dialog">
                <DialogHeader>
                  <DialogTitle>{editingId ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı Ekle'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label>Kullanıcı Adı</Label>
                    <Input
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      required
                      data-testid="username-field"
                    />
                  </div>
                  <div>
                    <Label>E-posta</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      data-testid="email-field"
                    />
                  </div>
                  <div>
                    <Label>Ad Soyad</Label>
                    <Input
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      required
                      data-testid="fullname-field"
                    />
                  </div>
                  <div>
                    <Label>Şifre {editingId && '(Boş bırakın değiştirmemek için)'}</Label>
                    <Input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required={!editingId}
                      data-testid="password-field"
                    />
                  </div>
                  <div>
                    <Label>Rol</Label>
                    <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                      <SelectTrigger data-testid="role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Yönetici</SelectItem>
                        <SelectItem value="regional_manager">Bölge Sorumlusu</SelectItem>
                        <SelectItem value="salesperson">Plasiyer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {(formData.role === 'regional_manager' || formData.role === 'salesperson') && (
                    <div>
                      <Label>Bölge</Label>
                      <Select value={formData.region_id} onValueChange={(value) => setFormData({ ...formData, region_id: value })}>
                        <SelectTrigger data-testid="region-select">
                          <SelectValue placeholder="Bölge seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          {regions.map((region) => (
                            <SelectItem key={region.id} value={region.id}>{region.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-user-button">
                      {editingId ? 'Güncelle' : 'Ekle'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        />

        {/* Users Table */}
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="users-table">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Ad Soyad</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Kullanıcı Adı</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">E-posta</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Rol</th>
                  {user.role === 'admin' && (
                    <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">İşlemler</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((userItem) => (
                  <tr key={userItem.id} className="hover:bg-gray-50 transition-colors" data-testid={`user-row-${userItem.username}`}>
                    <td className="px-6 py-4 text-sm text-gray-900">{userItem.full_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{userItem.username}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{userItem.email}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex px-3 py-1 rounded-full text-xs font-medium bg-red-50 text-[#E50019]">
                        {userItem.role === 'admin' ? 'Yönetici' : userItem.role === 'regional_manager' ? 'Bölge Sorumlusu' : 'Plasiyer'}
                      </span>
                    </td>
                    {user.role === 'admin' && (
                      <td className="px-6 py-4 text-right space-x-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEdit(userItem)}
                          data-testid={`edit-user-${userItem.username}`}
                        >
                          <Edit size={16} className="text-gray-600" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(userItem.id)}
                          data-testid={`delete-user-${userItem.username}`}
                        >
                          <Trash2 size={16} className="text-red-600" />
                        </Button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default UsersPage;
