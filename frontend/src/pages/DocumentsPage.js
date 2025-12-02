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
import { Plus, FileText, ExternalLink, Trash2 } from 'lucide-react';

const DocumentsPage = ({ user, setUser }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    url: '',
    type: 'katalog',
    file_base64: ''
  });
  const [uploadMode, setUploadMode] = useState('url'); // 'url' or 'upload'

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axiosInstance.get('/documents');
      setDocuments(response.data);
    } catch (error) {
      toast.error('Dokümanlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Dosya boyutu 10MB\'dan küçük olmalı');
      return;
    }
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result.split(',')[1]; // Get only base64 part
      setFormData({ 
        ...formData, 
        file_base64: base64String,
        file_name: file.name,
        file_type: file.type
      });
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        title: formData.title,
        description: formData.description || '',
        type: formData.type,
        url: uploadMode === 'url' ? formData.url : '',
        file_name: uploadMode === 'upload' ? formData.file_name : '',
        file_base64: uploadMode === 'upload' ? formData.file_base64 : '',
        file_type: uploadMode === 'upload' ? formData.file_type : ''
      };
      const response = await axiosInstance.post('/documents', data);
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      toast.success('Doküman eklendi');
      setDialogOpen(false);
      resetForm();
      fetchDocuments();
    } catch (error) {
      console.error('Doküman yükleme hatası:', error);
      toast.error(error.response?.data?.detail || 'İşlem başarısız');
    }
  };

  const handleDelete = async (docId, docTitle) => {
    if (!window.confirm(`'${docTitle}' dokümanını silmek istediğinizden emin misiniz?`)) {
      return;
    }
    try {
      await axiosInstance.delete(`/documents/${docId}`);
      toast.success(`'${docTitle}' dokümanı silindi`);
      fetchDocuments();
    } catch (error) {
      console.error('Doküman silme hatası:', error);
      toast.error(error.response?.data?.detail || 'Silme işlemi başarısız');
    }
  };
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      url: '',
      type: 'katalog',
      file_base64: '',
      file_name: '',
      file_type: ''
    });
    setUploadMode('url');
  };

  const getTypeLabel = (type) => {
    const labels = {
      katalog: 'Katalog',
      brosur: 'Broşür',
      fiyat_listesi: 'Fiyat Listesi'
    };
    return labels[type] || type;
  };

  const getTypeColor = (type) => {
    const colors = {
      katalog: 'bg-blue-50 text-blue-700',
      brosur: 'bg-green-50 text-green-700',
      fiyat_listesi: 'bg-purple-50 text-purple-700'
    };
    return colors[type] || 'bg-gray-50 text-gray-700';
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
      <div className="space-y-6" data-testid="documents-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dokümanlar</h1>
            <p className="text-gray-500 mt-1">Katalog, broşür ve fiyat listelerine erişin</p>
          </div>
          {user.role === 'admin' && (
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-[#E50019] hover:bg-[#c00015] text-white" data-testid="add-document-button">
                  <Plus size={20} className="mr-2" />
                  Yeni Doküman
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md" data-testid="document-dialog">
                <DialogHeader>
                  <DialogTitle>Yeni Doküman Ekle</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label>Başlık *</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      required
                      data-testid="document-title-field"
                    />
                  </div>
                  <div>
                    <Label>Açıklama</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={2}
                      data-testid="document-description-field"
                    />
                  </div>
                  
                  {/* Upload Mode Selector */}
                  <div>
                    <Label>Döküman Kaynağı *</Label>
                    <div className="flex gap-2 mt-2">
                      <Button
                        type="button"
                        variant={uploadMode === 'url' ? 'default' : 'outline'}
                        onClick={() => setUploadMode('url')}
                        className={uploadMode === 'url' ? 'bg-[#E50019]' : ''}
                      >
                        URL Bağlantısı
                      </Button>
                      <Button
                        type="button"
                        variant={uploadMode === 'upload' ? 'default' : 'outline'}
                        onClick={() => setUploadMode('upload')}
                        className={uploadMode === 'upload' ? 'bg-[#E50019]' : ''}
                      >
                        Dosya Yükle
                      </Button>
                    </div>
                  </div>

                  {uploadMode === 'url' ? (
                    <div>
                      <Label>URL *</Label>
                      <Input
                        type="url"
                        value={formData.url}
                        onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                        placeholder="https://..."
                        required
                        data-testid="document-url-field"
                      />
                    </div>
                  ) : (
                    <div>
                      <Label>Dosya Yükle *</Label>
                      <div className="mt-2">
                        <label className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-[#E50019] transition-colors">
                          <div className="text-center">
                            <FileText className="mx-auto text-gray-400 mb-2" size={32} />
                            <p className="text-sm text-gray-500">Dosya yükle (Maks 10MB)</p>
                            <p className="text-xs text-gray-400 mt-1">PDF, DOC, XLSX desteklenir</p>
                          </div>
                          <input
                            type="file"
                            accept=".pdf,.doc,.docx,.xlsx,.xls,.ppt,.pptx"
                            onChange={handleFileUpload}
                            className="hidden"
                            data-testid="document-file-input"
                          />
                        </label>
                        {formData.file_base64 && (
                          <p className="text-sm text-green-600 mt-2">✓ Dosya yüklendi</p>
                        )}
                      </div>
                    </div>
                  )}
                  <div>
                    <Label>Tip *</Label>
                    <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                      <SelectTrigger data-testid="document-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="katalog">Katalog</SelectItem>
                        <SelectItem value="brosur">Broşür</SelectItem>
                        <SelectItem value="fiyat_listesi">Fiyat Listesi</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="flex-1">
                      İptal
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#E50019] hover:bg-[#c00015]" data-testid="save-document-button">
                      Ekle
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Documents Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="documents-grid">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-xl border border-gray-100 p-6 hover:shadow-lg transition-shadow"
              data-testid={`document-card-${doc.title}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                  <FileText className="text-[#E50019]" size={24} />
                </div>
                <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getTypeColor(doc.type)}`}>
                  {getTypeLabel(doc.type)}
                </span>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{doc.title}</h3>
              <p className="text-sm text-gray-600 mb-4">{doc.description || 'Açıklama yok'}</p>
              <div className="flex justify-between items-center">
                <a
                  href={doc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-[#E50019] hover:underline"
                  data-testid={`view-document-${doc.title}`}
                >
                  Görüntüle <ExternalLink size={14} />
                </a>
                {user.role === 'admin' && (
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={(e) => { e.stopPropagation(); handleDelete(doc.id, doc.title); }}
                    className="text-gray-400 hover:text-red-500"
                    data-testid={`delete-document-${doc.title}`}
                  >
                    <Trash2 size={18} />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {documents.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <FileText size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Henüz doküman yok</h3>
            <p className="text-gray-500">Yeni bir doküman ekleyerek başlayın</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DocumentsPage;
