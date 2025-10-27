// BULK UPDATE DOSYASI - Bu değişiklikler otomatik uygulanacak

// VisitsPage.js - handleDelete ekle
const handleDelete_visits = async (visitId) => {
  if (!window.confirm('Bu ziyareti silmek istediğinizden emin misiniz?')) return;
  try {
    await axiosInstance.delete(`/visits/${visitId}`);
    toast.success('Ziyaret silindi');
    fetchVisits();
  } catch (error) {
    toast.error('Silme işlemi başarısız');
  }
};

// CollectionsPage.js - handleDelete ekle  
const handleDelete_collections = async (collectionId) => {
  if (!window.confirm('Bu tahsilatı silmek istediğinizden emin misiniz?')) return;
  try {
    await axiosInstance.delete(`/collections/${collectionId}`);
    toast.success('Tahsilat silindi');
    fetchCollections();
  } catch (error) {
    toast.error('Silme işlemi başarısız');
  }
};

// DocumentsPage.js - File upload base64 conversion
const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onloadend = () => {
    const base64 = reader.result.split(',')[1];
    setFormData({
      ...formData,
      file_base64: base64,
      file_name: file.name,
      file_type: file.type
    });
  };
  reader.readAsDataURL(file);
};
