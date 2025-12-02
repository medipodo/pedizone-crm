import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';

import LoginPage from '@/pages/LoginPage';
import Dashboard from '@/pages/Dashboard';
import UsersPage from '@/pages/UsersPage';
import RegionsPage from '@/pages/RegionsPage';
import CustomersPage from '@/pages/CustomersPage';
import ProductsPage from '@/pages/ProductsPage';
import VisitsPage from '@/pages/VisitsPage';
import SalesPage from '@/pages/SalesPage';
import CollectionsPage from '@/pages/CollectionsPage';
import ReportsPage from '@/pages/ReportsPage';
import DocumentsPage from '@/pages/DocumentsPage';
import CalendarPage from '@/pages/CalendarPage';

// Use relative path for API calls (Netlify will proxy to backend)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
export const API = `${BACKEND_URL}/api`;

export const axiosInstance = axios.create({
  baseURL: API,
});

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Inactivity timer - 1 saat işlem yapılmazsa otomatik logout
  useEffect(() => {
    if (!user) return;
    
    const INACTIVITY_TIMEOUT = 60 * 60 * 1000; // 1 saat (milliseconds)
    let inactivityTimer;
    
    const resetTimer = () => {
      if (inactivityTimer) clearTimeout(inactivityTimer);
      
      inactivityTimer = setTimeout(() => {
        // 1 saat işlem yapılmadı, logout yap
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        toast.info('Güvenlik nedeniyle oturumunuz sonlandırıldı. Lütfen tekrar giriş yapın.');
        window.location.href = '/login';
      }, INACTIVITY_TIMEOUT);
    };
    
    // Kullanıcı aktivitesi olduğunda timer'ı sıfırla
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      window.addEventListener(event, resetTimer);
    });
    
    // İlk timer'ı başlat
    resetTimer();
    
    // Cleanup
    return () => {
      if (inactivityTimer) clearTimeout(inactivityTimer);
      events.forEach(event => {
        window.removeEventListener(event, resetTimer);
      });
    };
  }, [user]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#E50019] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <LoginPage setUser={setUser} />} />
          <Route
            path="/dashboard"
            element={user ? <Dashboard user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/users"
            element={user ? <UsersPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/regions"
            element={user ? <RegionsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/customers"
            element={user ? <CustomersPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/products"
            element={user ? <ProductsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/visits"
            element={user ? <VisitsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/sales"
            element={user ? <SalesPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/collections"
            element={user ? <CollectionsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/reports"
            element={user ? <ReportsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/documents"
            element={user ? <DocumentsPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/calendar"
            element={user ? <CalendarPage user={user} setUser={setUser} /> : <Navigate to="/login" />}
          />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </>
  );
}

export default App;
