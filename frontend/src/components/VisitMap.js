import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Button } from '@/components/ui/button';

const VisitMap = ({ visits = [], sales = [], customers = [] }) => {
  const [mapReady, setMapReady] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all'); // all, gorusuldu, anlasildi, randevu_alindi

  useEffect(() => {
    setMapReady(true);
  }, []);

  // Türkiye genel koordinatları (merkez ve uzak zoom)
  const defaultCenter = [39.0, 35.0];
  const defaultZoom = 6;

  // Müşteri adını bul
  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Bilinmeyen Müşteri';
  };

  // Satış yapılan müşteri ID'lerini bul
  const salesCustomerIds = sales.map(s => s.customer_id);

  // Ziyaret durumunu belirle
  const getVisitStatus = (visit) => {
    // Önce status field'ı kontrol et
    if (visit.status === 'randevu_alindi') return 'randevu_alindi';
    if (visit.status === 'anlasildi') return 'anlasildi';
    
    // Satış varsa anlaşıldı
    if (salesCustomerIds.includes(visit.customer_id)) return 'anlasildi';
    
    // Status field varsa onu kullan
    if (visit.status) return visit.status;
    
    // Varsayılan olarak görüşüldü
    return 'gorusuldu';
  };

  // Duruma göre renk
  const getStatusColor = (status) => {
    switch (status) {
      case 'anlasildi': return '#E50019'; // Kırmızı
      case 'randevu_alindi': return '#3b82f6'; // Mavi
      case 'gorusuldu': return '#22c55e'; // Yeşil
      default: return '#22c55e';
    }
  };

  // Duruma göre etiket
  const getStatusLabel = (status) => {
    switch (status) {
      case 'anlasildi': return 'Anlaşıldı';
      case 'randevu_alindi': return 'Randevu Alındı';
      case 'gorusuldu': return 'Görüşüldü';
      default: return 'Görüşüldü';
    }
  };

  // Filtrelenmiş ziyaretler
  const filteredVisits = visits.filter(visit => {
    if (filterStatus === 'all') return true;
    const status = getVisitStatus(visit);
    return status === filterStatus;
  });

  if (!mapReady) {
    return (
      <div className="w-full h-96 bg-gray-100 rounded-xl flex items-center justify-center">
        <p className="text-gray-500">Harita yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Buttons */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button
          onClick={() => setFilterStatus('all')}
          variant={filterStatus === 'all' ? 'default' : 'outline'}
          size="sm"
          className={filterStatus === 'all' ? 'bg-gray-700' : ''}
        >
          Tümü ({visits.length})
        </Button>
        <Button
          onClick={() => setFilterStatus('gorusuldu')}
          variant={filterStatus === 'gorusuldu' ? 'default' : 'outline'}
          size="sm"
          className={filterStatus === 'gorusuldu' ? 'bg-green-600 hover:bg-green-700' : 'border-green-600 text-green-600'}
        >
          <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
          Görüşüldü ({visits.filter(v => getVisitStatus(v) === 'gorusuldu').length})
        </Button>
        <Button
          onClick={() => setFilterStatus('anlasildi')}
          variant={filterStatus === 'anlasildi' ? 'default' : 'outline'}
          size="sm"
          className={filterStatus === 'anlasildi' ? 'bg-[#E50019] hover:bg-[#c00015]' : 'border-[#E50019] text-[#E50019]'}
        >
          <span className="w-3 h-3 rounded-full bg-[#E50019] mr-2"></span>
          Anlaşıldı ({visits.filter(v => getVisitStatus(v) === 'anlasildi').length})
        </Button>
        <Button
          onClick={() => setFilterStatus('randevu_alindi')}
          variant={filterStatus === 'randevu_alindi' ? 'default' : 'outline'}
          size="sm"
          className={filterStatus === 'randevu_alindi' ? 'bg-blue-600 hover:bg-blue-700' : 'border-blue-600 text-blue-600'}
        >
          <span className="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
          Randevu Alındı ({visits.filter(v => getVisitStatus(v) === 'randevu_alindi').length})
        </Button>
      </div>

      {/* Map */}
      <div className="w-full h-96 rounded-xl overflow-hidden border border-gray-200" data-testid="visit-map">
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Ziyaret noktaları */}
          {filteredVisits.map((visit) => {
            // Location object veya direkt latitude/longitude olabilir
            const lat = visit.location?.latitude || visit.latitude;
            const lng = visit.location?.longitude || visit.longitude;
            
            if (!lat || !lng) return null;
            
            const status = getVisitStatus(visit);
            const color = getStatusColor(status);
            const label = getStatusLabel(status);
            
            return (
              <CircleMarker
                key={visit.id}
                center={[parseFloat(lat), parseFloat(lng)]}
                radius={8}
                fillColor={color}
                color="#fff"
                weight={2}
                opacity={1}
                fillOpacity={0.8}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-semibold">{getCustomerName(visit.customer_id)}</p>
                    <p className="text-xs text-gray-600">
                      {new Date(visit.visit_date).toLocaleDateString('tr-TR')}
                    </p>
                    <p className="text-xs mt-1">
                      <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: color }}></span>
                      {label}
                    </p>
                    {visit.notes && (
                      <p className="text-xs text-gray-500 mt-1">{visit.notes.substring(0, 50)}</p>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};

export default VisitMap;
