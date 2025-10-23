import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { axiosInstance } from '@/App';
import { toast } from 'sonner';
import { Calendar } from '@/components/ui/calendar';
import { Card } from '@/components/ui/card';

const CalendarPage = ({ user, setUser }) => {
  const [date, setDate] = useState(new Date());
  const [visits, setVisits] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVisits();
    fetchCustomers();
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

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : '-';
  };

  const getVisitsForDate = (selectedDate) => {
    if (!selectedDate) return [];
    const dateStr = selectedDate.toISOString().split('T')[0];
    return visits.filter(visit => visit.visit_date === dateStr);
  };

  const selectedDateVisits = getVisitsForDate(date);

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
      <div className="space-y-6" data-testid="calendar-page">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ziyaret Takvimi</h1>
          <p className="text-gray-500 mt-1">Ziyaretleri takvim üzerinden görüntüleyin</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <Calendar
                mode="single"
                selected={date}
                onSelect={setDate}
                className="rounded-xl border-0"
                modifiers={{
                  hasVisit: visits.map(v => new Date(v.visit_date))
                }}
                modifiersStyles={{
                  hasVisit: {
                    backgroundColor: '#E50019',
                    color: 'white',
                    fontWeight: 'bold'
                  }
                }}
              />
            </Card>
          </div>

          {/* Visits for Selected Date */}
          <div className="lg:col-span-1">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {date ? date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Tarih seçin'}
              </h3>
              <div className="space-y-3">
                {selectedDateVisits.length > 0 ? (
                  selectedDateVisits.map((visit) => (
                    <div
                      key={visit.id}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-100"
                      data-testid={`calendar-visit-${visit.id}`}
                    >
                      <p className="font-semibold text-gray-900">{getCustomerName(visit.customer_id)}</p>
                      {visit.notes && (
                        <p className="text-sm text-gray-600 mt-1">{visit.notes}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Bu tarihte ziyaret yok</p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Upcoming Visits */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Yaklaşan Ziyaretler</h3>
          <div className="space-y-3">
            {visits
              .filter(v => new Date(v.visit_date) >= new Date())
              .sort((a, b) => new Date(a.visit_date) - new Date(b.visit_date))
              .slice(0, 5)
              .map((visit) => (
                <div
                  key={visit.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100"
                  data-testid={`upcoming-visit-${visit.id}`}
                >
                  <div>
                    <p className="font-semibold text-gray-900">{getCustomerName(visit.customer_id)}</p>
                    {visit.notes && (
                      <p className="text-sm text-gray-600 mt-1">{visit.notes}</p>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(visit.visit_date).toLocaleDateString('tr-TR')}
                  </span>
                </div>
              ))}
            {visits.filter(v => new Date(v.visit_date) >= new Date()).length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">Yaklaşan ziyaret yok</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default CalendarPage;
