import React, { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Car, Shield, DollarSign, MapPin, Bell, User, LogOut, Menu, X, 
  CheckCircle, Clock, AlertCircle, Camera, ChevronRight, ChevronLeft,
  Star, FileText, Phone, Mail, Search, Filter, Eye, Plus
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom Leaflet Icon
const createCustomIcon = (color = '#FFBF00') => {
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 3px solid #0A0A0A;
      box-shadow: 0 0 20px rgba(255, 191, 0, 0.5);
      animation: pulse 2s infinite;
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

// Toast Component
const Toast = ({ message, type = 'info', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const colors = {
    success: 'border-green-500 bg-green-500/10',
    error: 'border-red-500 bg-red-500/10',
    info: 'border-amber-500 bg-amber-500/10',
  };

  return (
    <div className={`fixed top-4 right-4 z-50 p-4 rounded-xl border ${colors[type]} fade-in`}>
      <p className="text-white">{message}</p>
    </div>
  );
};

// Notification Bell Component
const NotificationBell = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchNotifications = async () => {
    try {
      const res = await axios.get(`${API}/notifications/${user.id}`);
      setNotifications(res.data);
      setUnreadCount(res.data.filter(n => !n.read).length);
    } catch (e) {
      console.error('Error fetching notifications:', e);
    }
  };

  const markAsRead = async (id) => {
    try {
      await axios.post(`${API}/notifications/${id}/read`);
      fetchNotifications();
    } catch (e) {
      console.error('Error marking notification as read:', e);
    }
  };

  return (
    <div className="relative">
      <button
        data-testid="notification-bell"
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 rounded-full hover:bg-[#1A1A1A] transition-colors"
      >
        <Bell className="w-6 h-6 text-white" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#FFBF00] text-[#0A0A0A] text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-[#141414] border border-[#262626] rounded-xl shadow-2xl z-50 max-h-96 overflow-y-auto">
          <div className="p-4 border-b border-[#262626]">
            <h3 className="font-bold text-white">Bildirimler</h3>
          </div>
          {notifications.length === 0 ? (
            <p className="p-4 text-[#A3A3A3] text-center">Bildirim yok</p>
          ) : (
            notifications.map(notif => (
              <div
                key={notif.id}
                onClick={() => markAsRead(notif.id)}
                className={`p-4 border-b border-[#262626] cursor-pointer hover:bg-[#1A1A1A] transition-colors ${!notif.read ? 'bg-[#1A1A1A]' : ''}`}
              >
                <p className="font-semibold text-white text-sm">{notif.title}</p>
                <p className="text-[#A3A3A3] text-xs mt-1">{notif.message}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);

  return (
    <header className="glass-header fixed top-0 left-0 right-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => navigate('/')}
            data-testid="logo"
          >
            <div className="w-10 h-10 bg-[#FFBF00] rounded-xl flex items-center justify-center">
              <Car className="w-6 h-6 text-[#0A0A0A]" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">AutoCheck</span>
          </div>

          {user ? (
            <div className="flex items-center gap-4">
              <NotificationBell />
              <div className="relative">
                <button
                  data-testid="user-menu-btn"
                  onClick={() => setShowMenu(!showMenu)}
                  className="flex items-center gap-2 p-2 rounded-xl hover:bg-[#1A1A1A] transition-colors"
                >
                  <div className="w-8 h-8 bg-[#262626] rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-[#FFBF00]" />
                  </div>
                  <span className="text-white hidden sm:block">{user.full_name}</span>
                </button>

                {showMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-[#141414] border border-[#262626] rounded-xl shadow-2xl">
                    <div className="p-3 border-b border-[#262626]">
                      <p className="text-sm text-[#A3A3A3]">{user.user_type === 'buyer' ? 'Alıcı' : 'Kontrolcü'}</p>
                      <p className="text-white font-medium truncate">{user.email}</p>
                    </div>
                    <button
                      data-testid="logout-btn"
                      onClick={() => { logout(); navigate('/'); setShowMenu(false); }}
                      className="w-full p-3 text-left text-red-400 hover:bg-[#1A1A1A] flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Çıkış Yap
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button
                data-testid="login-btn"
                onClick={() => navigate('/login')}
                className="px-4 py-2 text-white hover:text-[#FFBF00] transition-colors"
              >
                Giriş
              </button>
              <button
                data-testid="signup-btn"
                onClick={() => navigate('/register')}
                className="px-4 py-2 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active"
              >
                Kayıt Ol
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

// Landing Page
const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      navigate(user.user_type === 'buyer' ? '/buyer' : '/inspector');
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: `url('https://images.unsplash.com/photo-1623659248894-1a0272243054?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHw0fHx5ZWxsb3clMjBzcG9ydHMlMjBjYXIlMjBuaWdodHxlbnwwfHx8fDE3NzQ1NjE3OTh8MA&ixlib=rb-4.1.0&q=85')`
          }}
        />
        <div className="absolute inset-0 bg-black/70" />
        
        <div className="relative z-10 max-w-5xl mx-auto px-4 text-center pt-20">
          <p className="overline mb-4">Güvenilir Uzaktan Araç Kontrol</p>
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-white tracking-tighter leading-none mb-6">
            Aracı Almadan<br />
            <span className="text-[#FFBF00]">Kontrol Ettir</span>
          </h1>
          <p className="text-lg sm:text-xl text-[#A3A3A3] max-w-2xl mx-auto mb-10">
            Uzaktaki aracı profesyonel kontrolcülerimize incelet. 
            Detaylı rapor al, güvenle satın al.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              data-testid="cta-request-inspection"
              onClick={() => navigate('/register?type=buyer')}
              className="px-8 py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold text-lg rounded-xl hover:bg-[#FFD147] transition-all btn-active shadow-lg shadow-amber-500/20"
            >
              Kontrol Talep Et
            </button>
            <button
              data-testid="cta-become-inspector"
              onClick={() => navigate('/register?type=inspector')}
              className="px-8 py-4 bg-transparent text-white font-bold text-lg rounded-xl border-2 border-white hover:border-[#FFBF00] hover:text-[#FFBF00] transition-all"
            >
              Kontrolcü Ol
            </button>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="overline mb-4">Nasıl Çalışır?</p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
              3 Adımda Araç Kontrolü
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 stagger-children">
            {[
              { icon: FileText, title: 'Talep Oluştur', desc: 'Araç bilgilerini ve satıcı adresini gir, paketini seç.' },
              { icon: User, title: 'Kontrolcü Eşleşmesi', desc: 'Yakındaki onaylı kontrolcüler bildirim alır ve işi kabul eder.' },
              { icon: CheckCircle, title: 'Rapor Al', desc: 'Detaylı fotoğraf ve video içeren raporu incele, kararını ver.' },
            ].map((item, i) => (
              <div key={i} className="bg-[#141414] border border-[#262626] rounded-2xl p-8 card-hover">
                <div className="w-14 h-14 bg-[#FFBF00]/10 rounded-xl flex items-center justify-center mb-6">
                  <item.icon className="w-7 h-7 text-[#FFBF00]" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                <p className="text-[#A3A3A3]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Packages Preview */}
      <section className="py-24 bg-[#141414]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="overline mb-4">Paketler</p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
              İhtiyacına Uygun Paket
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { name: 'Basic', price: 100, features: ['Dış görünüm kontrolü', 'İç mekan kontrolü', 'Temel motor kontrolü', 'Test sürüşü', '15 fotoğraf'] },
              { name: 'Premium', price: 250, features: ['Tüm Basic özellikler', 'Detaylı motor incelemesi', 'Alt kısım kontrolü', 'Sıvı seviyeleri', '30 fotoğraf', 'Video'] },
              { name: 'Professional', price: 300, features: ['Tüm Premium özellikler', 'OBD-II tanılama', 'Şase kontrolü', 'Boya kalınlığı ölçümü', '50+ fotoğraf', 'Video görüşme'], isPro: true },
            ].map((pkg, i) => (
              <div 
                key={i} 
                className={`bg-[#0A0A0A] border rounded-2xl p-8 card-hover ${pkg.isPro ? 'professional-glow' : 'border-[#262626]'}`}
              >
                {pkg.isPro && <p className="overline mb-4">En Popüler</p>}
                <h3 className="text-2xl font-bold text-white mb-2">{pkg.name}</h3>
                <p className="text-4xl font-bold text-[#FFBF00] mb-6">${pkg.price}</p>
                <ul className="space-y-3">
                  {pkg.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-3 text-[#A3A3A3]">
                      <CheckCircle className="w-5 h-5 text-[#FFBF00] flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA for Inspectors */}
      <section className="py-24 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="overline mb-4">Kontrolcü Ol</p>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight mb-6">
                Araç Bilginle<br />
                <span className="text-[#FFBF00]">Para Kazan</span>
              </h2>
              <p className="text-lg text-[#A3A3A3] mb-8">
                Esnek saatlerde çalış, kendi işini kendin seç. 
                Her kontrol başına $80-$240 kazan.
              </p>
              <button
                data-testid="cta-join-inspectors"
                onClick={() => navigate('/register?type=inspector')}
                className="px-8 py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold text-lg rounded-xl hover:bg-[#FFD147] transition-all btn-active"
              >
                Hemen Başla
              </button>
            </div>
            <div className="rounded-2xl overflow-hidden">
              <img 
                src="https://images.pexels.com/photos/4895408/pexels-photo-4895408.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
                alt="Inspector checking car"
                className="w-full h-auto"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-[#141414] border-t border-[#262626]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#FFBF00] rounded-xl flex items-center justify-center">
                <Car className="w-6 h-6 text-[#0A0A0A]" />
              </div>
              <span className="text-xl font-bold text-white">AutoCheck</span>
            </div>
            <p className="text-[#A3A3A3]">© 2026 AutoCheck. Tüm hakları saklıdır.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Auth Pages
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post(`${API}/auth/login`, { email, password });
      login(res.data);
      navigate(res.data.user_type === 'buyer' ? '/buyer' : '/inspector');
    } catch (e) {
      setError(e.response?.data?.detail || 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20">
      <div className="w-full max-w-md">
        <div className="bg-[#141414] border border-[#262626] rounded-2xl p-8">
          <h1 className="text-3xl font-bold text-white mb-2">Giriş Yap</h1>
          <p className="text-[#A3A3A3] mb-8">Hesabına giriş yap</p>

          {error && (
            <div className="bg-red-500/10 border border-red-500 rounded-xl p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Email</label>
              <input
                data-testid="login-email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Şifre</label>
              <input
                data-testid="login-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <button
              data-testid="login-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active disabled:opacity-50"
            >
              {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
            </button>
          </form>

          <p className="text-center text-[#A3A3A3] mt-6">
            Hesabın yok mu?{' '}
            <button onClick={() => navigate('/register')} className="text-[#FFBF00] hover:underline">
              Kayıt ol
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    user_type: new URLSearchParams(window.location.search).get('type') || 'buyer'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post(`${API}/auth/register`, formData);
      login(res.data);
      navigate(res.data.user_type === 'buyer' ? '/buyer' : '/inspector');
    } catch (e) {
      setError(e.response?.data?.detail || 'Kayıt başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20 pb-12">
      <div className="w-full max-w-md">
        <div className="bg-[#141414] border border-[#262626] rounded-2xl p-8">
          <h1 className="text-3xl font-bold text-white mb-2">Kayıt Ol</h1>
          <p className="text-[#A3A3A3] mb-8">Yeni hesap oluştur</p>

          {error && (
            <div className="bg-red-500/10 border border-red-500 rounded-xl p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Hesap Tipi</label>
              <div className="grid grid-cols-2 gap-4">
                {['buyer', 'inspector'].map(type => (
                  <button
                    key={type}
                    type="button"
                    data-testid={`register-type-${type}`}
                    onClick={() => setFormData({...formData, user_type: type})}
                    className={`py-3 px-4 rounded-xl border-2 font-medium transition-all ${
                      formData.user_type === type 
                        ? 'border-[#FFBF00] bg-[#FFBF00]/10 text-[#FFBF00]' 
                        : 'border-[#262626] text-[#A3A3A3] hover:border-[#A3A3A3]'
                    }`}
                  >
                    {type === 'buyer' ? 'Alıcı' : 'Kontrolcü'}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Ad Soyad</label>
              <input
                data-testid="register-name-input"
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Email</label>
              <input
                data-testid="register-email-input"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Telefon</label>
              <input
                data-testid="register-phone-input"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Şifre</label>
              <input
                data-testid="register-password-input"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                required
              />
            </div>
            <button
              data-testid="register-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active disabled:opacity-50"
            >
              {loading ? 'Kayıt yapılıyor...' : 'Kayıt Ol'}
            </button>
          </form>

          <p className="text-center text-[#A3A3A3] mt-6">
            Zaten hesabın var mı?{' '}
            <button onClick={() => navigate('/login')} className="text-[#FFBF00] hover:underline">
              Giriş yap
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Buyer Dashboard
const BuyerDashboard = () => {
  const { user } = useAuth();
  const [inspections, setInspections] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedInspection, setSelectedInspection] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchInspections();
  }, [user]);

  const fetchInspections = async () => {
    try {
      const res = await axios.get(`${API}/inspections/buyer/${user.id}`);
      setInspections(res.data);
    } catch (e) {
      console.error('Error fetching inspections:', e);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'status-pending', text: 'Bekliyor' },
      accepted: { class: 'status-accepted', text: 'Kabul Edildi' },
      in_progress: { class: 'status-in-progress', text: 'Devam Ediyor' },
      completed: { class: 'status-completed', text: 'Tamamlandı' },
    };
    const badge = badges[status] || badges.pending;
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.class}`}>{badge.text}</span>;
  };

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Hoş geldin, {user.full_name}</h1>
            <p className="text-[#A3A3A3]">Araç kontrollerini yönet</p>
          </div>
          <button
            data-testid="new-inspection-btn"
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-6 py-3 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active"
          >
            <Plus className="w-5 h-5" />
            Yeni Kontrol Talebi
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
          {[
            { label: 'Toplam Talep', value: inspections.length, icon: FileText },
            { label: 'Devam Eden', value: inspections.filter(i => ['pending', 'accepted', 'in_progress'].includes(i.status)).length, icon: Clock },
            { label: 'Tamamlanan', value: inspections.filter(i => i.status === 'completed').length, icon: CheckCircle },
          ].map((stat, i) => (
            <div key={i} className="bg-[#141414] border border-[#262626] rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[#A3A3A3] text-sm">{stat.label}</p>
                  <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className="w-12 h-12 bg-[#FFBF00]/10 rounded-xl flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-[#FFBF00]" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Inspections List */}
        <div className="bg-[#141414] border border-[#262626] rounded-2xl">
          <div className="p-6 border-b border-[#262626]">
            <h2 className="text-xl font-bold text-white">Kontrol Taleplerim</h2>
          </div>
          
          {inspections.length === 0 ? (
            <div className="p-12 text-center">
              <Car className="w-16 h-16 text-[#262626] mx-auto mb-4" />
              <p className="text-[#A3A3A3]">Henüz kontrol talebiniz yok</p>
              <button
                onClick={() => setShowForm(true)}
                className="mt-4 text-[#FFBF00] hover:underline"
              >
                İlk talebini oluştur
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#262626]">
              {inspections.map(inspection => (
                <div 
                  key={inspection.id} 
                  className="p-6 hover:bg-[#1A1A1A] transition-colors cursor-pointer"
                  onClick={() => setSelectedInspection(inspection)}
                  data-testid={`inspection-item-${inspection.id}`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-[#262626] rounded-xl flex items-center justify-center">
                        <Car className="w-6 h-6 text-[#FFBF00]" />
                      </div>
                      <div>
                        <p className="font-bold text-white">
                          {inspection.vehicle.year} {inspection.vehicle.make} {inspection.vehicle.model}
                        </p>
                        <p className="text-sm text-[#A3A3A3]">
                          {inspection.seller.city}, {inspection.seller.state}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {getStatusBadge(inspection.status)}
                      <p className="font-bold text-[#FFBF00]">${inspection.total_amount}</p>
                      <ChevronRight className="w-5 h-5 text-[#A3A3A3]" />
                    </div>
                  </div>
                  {inspection.status === 'pending' && (
                    <div className="mt-4 p-4 bg-[#FFBF00]/10 border border-[#FFBF00]/30 rounded-xl">
                      <p className="text-sm text-[#FFBF00]">
                        <strong>Güvenlik Kodu:</strong> {inspection.security_code}
                      </p>
                      <p className="text-xs text-[#A3A3A3] mt-1">
                        Bu kodu satıcıya iletin. Satıcı, kontrolcüye bu kodu verecektir.
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* New Inspection Form Modal */}
        {showForm && (
          <InspectionForm 
            onClose={() => setShowForm(false)} 
            onSuccess={() => {
              setShowForm(false);
              fetchInspections();
              setToast({ message: 'Kontrol talebi oluşturuldu!', type: 'success' });
            }}
            userId={user.id}
          />
        )}

        {/* Inspection Detail Modal */}
        {selectedInspection && (
          <InspectionDetail 
            inspection={selectedInspection} 
            onClose={() => setSelectedInspection(null)} 
          />
        )}

        {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      </div>
    </div>
  );
};

// Inspection Form
const InspectionForm = ({ onClose, onSuccess, userId }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    vehicle: { make: '', model: '', year: 2020, vin: '', color: '', mileage: '' },
    seller: { name: '', phone: '', address: '', city: '', state: '', zip_code: '', lat: 41.8781, lng: -87.6298 },
    package_type: 'basic',
    tip_amount: 0,
    preferred_date: '',
    notes: ''
  });

  const packages = [
    { id: 'basic', name: 'Basic', price: 100, features: ['Dış görünüm', 'İç mekan', 'Motor', 'Test sürüşü', '15 fotoğraf'] },
    { id: 'premium', name: 'Premium', price: 250, features: ['Tüm Basic', 'Detaylı motor', 'Alt kısım', 'Sıvılar', '30 fotoğraf', 'Video'] },
    { id: 'professional', name: 'Professional', price: 300, features: ['Tüm Premium', 'OBD-II', 'Şase', 'Boya ölçüm', '50+ fotoğraf', 'Video görüşme'], isPro: true },
  ];

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/inspections?buyer_id=${userId}`, formData);
      onSuccess();
    } catch (e) {
      console.error('Error creating inspection:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#141414] border border-[#262626] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-[#262626] flex items-center justify-between sticky top-0 bg-[#141414] z-10">
          <div>
            <h2 className="text-xl font-bold text-white">Yeni Kontrol Talebi</h2>
            <p className="text-sm text-[#A3A3A3]">Adım {step}/4</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[#262626] rounded-full">
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <div className="p-6">
          {/* Step 1: Vehicle Info */}
          {step === 1 && (
            <div className="space-y-6 fade-in">
              <h3 className="text-lg font-bold text-white">Araç Bilgileri</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Marka</label>
                  <input
                    data-testid="vehicle-make-input"
                    type="text"
                    value={formData.vehicle.make}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, make: e.target.value}})}
                    placeholder="Toyota"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Model</label>
                  <input
                    data-testid="vehicle-model-input"
                    type="text"
                    value={formData.vehicle.model}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, model: e.target.value}})}
                    placeholder="Camry"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Yıl</label>
                  <input
                    data-testid="vehicle-year-input"
                    type="number"
                    value={formData.vehicle.year}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, year: parseInt(e.target.value)}})}
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Renk</label>
                  <input
                    data-testid="vehicle-color-input"
                    type="text"
                    value={formData.vehicle.color}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, color: e.target.value}})}
                    placeholder="Siyah"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">VIN (Opsiyonel)</label>
                  <input
                    data-testid="vehicle-vin-input"
                    type="text"
                    value={formData.vehicle.vin}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, vin: e.target.value}})}
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Kilometre</label>
                  <input
                    data-testid="vehicle-mileage-input"
                    type="number"
                    value={formData.vehicle.mileage}
                    onChange={(e) => setFormData({...formData, vehicle: {...formData.vehicle, mileage: parseInt(e.target.value) || ''}})}
                    placeholder="50000"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Seller Info */}
          {step === 2 && (
            <div className="space-y-6 fade-in">
              <h3 className="text-lg font-bold text-white">Satıcı Bilgileri</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Satıcı Adı</label>
                  <input
                    data-testid="seller-name-input"
                    type="text"
                    value={formData.seller.name}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, name: e.target.value}})}
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Telefon</label>
                  <input
                    data-testid="seller-phone-input"
                    type="tel"
                    value={formData.seller.phone}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, phone: e.target.value}})}
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Şehir</label>
                  <input
                    data-testid="seller-city-input"
                    type="text"
                    value={formData.seller.city}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, city: e.target.value}})}
                    placeholder="Chicago"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Adres</label>
                  <input
                    data-testid="seller-address-input"
                    type="text"
                    value={formData.seller.address}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, address: e.target.value}})}
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Eyalet</label>
                  <input
                    data-testid="seller-state-input"
                    type="text"
                    value={formData.seller.state}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, state: e.target.value}})}
                    placeholder="IL"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-2">ZIP Kodu</label>
                  <input
                    data-testid="seller-zip-input"
                    type="text"
                    value={formData.seller.zip_code}
                    onChange={(e) => setFormData({...formData, seller: {...formData.seller, zip_code: e.target.value}})}
                    placeholder="60601"
                    className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white"
                    required
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Package Selection */}
          {step === 3 && (
            <div className="space-y-6 fade-in">
              <h3 className="text-lg font-bold text-white">Paket Seçimi</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {packages.map(pkg => (
                  <div
                    key={pkg.id}
                    data-testid={`package-${pkg.id}`}
                    onClick={() => setFormData({...formData, package_type: pkg.id})}
                    className={`p-6 rounded-2xl border-2 cursor-pointer transition-all ${
                      formData.package_type === pkg.id 
                        ? 'border-[#FFBF00] bg-[#FFBF00]/10' 
                        : pkg.isPro ? 'professional-glow' : 'border-[#262626] hover:border-[#A3A3A3]'
                    }`}
                  >
                    {pkg.isPro && <p className="overline mb-2">Önerilen</p>}
                    <h4 className="font-bold text-white">{pkg.name}</h4>
                    <p className="text-2xl font-bold text-[#FFBF00] my-3">${pkg.price}</p>
                    <ul className="space-y-2">
                      {pkg.features.map((f, i) => (
                        <li key={i} className="text-sm text-[#A3A3A3] flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-[#FFBF00]" />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Bahşiş (Opsiyonel)</label>
                <div className="flex gap-3">
                  {[0, 10, 20, 30].map(amount => (
                    <button
                      key={amount}
                      type="button"
                      data-testid={`tip-${amount}`}
                      onClick={() => setFormData({...formData, tip_amount: amount})}
                      className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all ${
                        formData.tip_amount === amount 
                          ? 'border-[#FFBF00] bg-[#FFBF00]/10 text-[#FFBF00]' 
                          : 'border-[#262626] text-[#A3A3A3] hover:border-[#A3A3A3]'
                      }`}
                    >
                      {amount === 0 ? 'Yok' : `$${amount}`}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div className="space-y-6 fade-in">
              <h3 className="text-lg font-bold text-white">Özet</h3>
              
              <div className="space-y-4">
                <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-4">
                  <p className="text-[#A3A3A3] text-sm mb-1">Araç</p>
                  <p className="text-white font-medium">
                    {formData.vehicle.year} {formData.vehicle.make} {formData.vehicle.model} - {formData.vehicle.color}
                  </p>
                </div>

                <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-4">
                  <p className="text-[#A3A3A3] text-sm mb-1">Konum</p>
                  <p className="text-white font-medium">
                    {formData.seller.address}, {formData.seller.city}, {formData.seller.state} {formData.seller.zip_code}
                  </p>
                </div>

                <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[#A3A3A3]">Paket ({packages.find(p => p.id === formData.package_type)?.name})</span>
                    <span className="text-white font-medium">${packages.find(p => p.id === formData.package_type)?.price}</span>
                  </div>
                  {formData.tip_amount > 0 && (
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-[#A3A3A3]">Bahşiş</span>
                      <span className="text-white font-medium">${formData.tip_amount}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-[#262626]">
                    <span className="text-white font-bold">Toplam</span>
                    <span className="text-[#FFBF00] font-bold text-xl">
                      ${packages.find(p => p.id === formData.package_type)?.price + formData.tip_amount}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Notlar (Opsiyonel)</label>
                <textarea
                  data-testid="notes-input"
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Kontrolcüye iletmek istediğiniz notlar..."
                  className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white h-24 resize-none"
                />
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-[#262626] flex justify-between">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="flex items-center gap-2 px-6 py-3 text-white hover:text-[#FFBF00] transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              Geri
            </button>
          ) : (
            <div />
          )}
          
          {step < 4 ? (
            <button
              data-testid="form-next-btn"
              onClick={() => setStep(step + 1)}
              className="flex items-center gap-2 px-6 py-3 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active"
            >
              İleri
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <button
              data-testid="form-submit-btn"
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active disabled:opacity-50"
            >
              {loading ? 'Oluşturuluyor...' : 'Talep Oluştur'}
              <CheckCircle className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Inspection Detail Modal
const InspectionDetail = ({ inspection, onClose }) => {
  const [report, setReport] = useState(null);

  useEffect(() => {
    if (inspection.status === 'completed') {
      fetchReport();
    }
  }, [inspection]);

  const fetchReport = async () => {
    try {
      const res = await axios.get(`${API}/reports/inspection/${inspection.id}`);
      setReport(res.data);
    } catch (e) {
      console.error('Error fetching report:', e);
    }
  };

  const getRecBadge = (rec) => {
    const badges = {
      buy: { class: 'rec-buy', text: 'Alınabilir' },
      caution: { class: 'rec-caution', text: 'Dikkatli Ol' },
      avoid: { class: 'rec-avoid', text: 'Kaçın' },
    };
    const badge = badges[rec] || badges.caution;
    return <span className={`px-4 py-2 rounded-full text-sm font-bold ${badge.class}`}>{badge.text}</span>;
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#141414] border border-[#262626] rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-[#262626] flex items-center justify-between sticky top-0 bg-[#141414] z-10">
          <h2 className="text-xl font-bold text-white">Kontrol Detayı</h2>
          <button onClick={onClose} className="p-2 hover:bg-[#262626] rounded-full">
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Vehicle Info */}
          <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Araç Bilgileri</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[#A3A3A3] text-sm">Marka / Model</p>
                <p className="text-white font-medium">{inspection.vehicle.make} {inspection.vehicle.model}</p>
              </div>
              <div>
                <p className="text-[#A3A3A3] text-sm">Yıl / Renk</p>
                <p className="text-white font-medium">{inspection.vehicle.year} - {inspection.vehicle.color}</p>
              </div>
            </div>
          </div>

          {/* Security Code (for pending/accepted) */}
          {['pending', 'accepted'].includes(inspection.status) && (
            <div className="bg-[#FFBF00]/10 border border-[#FFBF00]/30 rounded-xl p-6">
              <h3 className="text-lg font-bold text-[#FFBF00] mb-2">Güvenlik Kodu</h3>
              <p className="text-4xl font-mono font-bold text-white tracking-widest">{inspection.security_code}</p>
              <p className="text-sm text-[#A3A3A3] mt-3">
                Bu kodu satıcıya iletin. Kontrolcü bu kod olmadan kontrole başlayamaz.
              </p>
            </div>
          )}

          {/* Inspector Info */}
          {inspection.inspector_name && (
            <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Kontrolcü</h3>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#262626] rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-[#FFBF00]" />
                </div>
                <div>
                  <p className="text-white font-medium">{inspection.inspector_name}</p>
                  <p className="text-[#A3A3A3] text-sm">Kontrolcü</p>
                </div>
              </div>
            </div>
          )}

          {/* Report */}
          {report && (
            <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-white">Kontrol Raporu</h3>
                {getRecBadge(report.recommendation)}
              </div>
              
              <div className="space-y-4">
                {report.steps?.map((step, i) => (
                  <div key={i} className="border border-[#262626] rounded-xl p-4">
                    <p className="font-medium text-white mb-2">{step.description}</p>
                    {step.photos?.length > 0 && (
                      <div className="flex gap-2 flex-wrap mb-2">
                        {step.photos.map((photo, j) => (
                          <img 
                            key={j} 
                            src={`${BACKEND_URL}${photo}`} 
                            alt={`Step ${i} photo ${j}`}
                            className="w-20 h-20 object-cover rounded-lg"
                          />
                        ))}
                      </div>
                    )}
                    {step.notes && <p className="text-[#A3A3A3] text-sm">{step.notes}</p>}
                  </div>
                ))}
              </div>

              {report.overall_notes && (
                <div className="mt-6 pt-6 border-t border-[#262626]">
                  <h4 className="font-bold text-white mb-2">Genel Değerlendirme</h4>
                  <p className="text-[#A3A3A3]">{report.overall_notes}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Inspector Dashboard
const InspectorDashboard = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [availableJobs, setAvailableJobs] = useState([]);
  const [myJobs, setMyJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [activeTab, setActiveTab] = useState('available');
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchProfile();
    fetchAvailableJobs();
    fetchMyJobs();
  }, [user]);

  const fetchProfile = async () => {
    try {
      const res = await axios.get(`${API}/inspector/profile/${user.id}`);
      setProfile(res.data);
    } catch (e) {
      console.error('Error fetching profile:', e);
    }
  };

  const fetchAvailableJobs = async () => {
    try {
      const res = await axios.get(`${API}/inspections/available`);
      setAvailableJobs(res.data);
    } catch (e) {
      console.error('Error fetching jobs:', e);
    }
  };

  const fetchMyJobs = async () => {
    try {
      const res = await axios.get(`${API}/inspector/jobs/${user.id}`);
      setMyJobs(res.data);
    } catch (e) {
      console.error('Error fetching my jobs:', e);
    }
  };

  const handleAcceptJob = async (jobId) => {
    try {
      await axios.post(`${API}/inspections/${jobId}/accept?inspector_id=${user.id}`);
      setToast({ message: 'İş kabul edildi!', type: 'success' });
      fetchAvailableJobs();
      fetchMyJobs();
      setSelectedJob(null);
    } catch (e) {
      setToast({ message: e.response?.data?.detail || 'Hata oluştu', type: 'error' });
    }
  };

  const handleVerifyId = async () => {
    try {
      await axios.post(`${API}/inspector/verify-id/${user.id}`);
      fetchProfile();
      setShowVerifyModal(false);
      setToast({ message: 'Kimlik onaylandı!', type: 'success' });
    } catch (e) {
      setToast({ message: 'Onaylama başarısız', type: 'error' });
    }
  };

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Kontrolcü Paneli</h1>
            <p className="text-[#A3A3A3]">Merhaba, {user.full_name}</p>
          </div>
          {profile && !profile.id_verified && (
            <button
              data-testid="verify-id-btn"
              onClick={() => setShowVerifyModal(true)}
              className="flex items-center gap-2 px-6 py-3 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active"
            >
              <Shield className="w-5 h-5" />
              Kimlik Onayla
            </button>
          )}
        </div>

        {/* Stats */}
        {profile && (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-8">
            {[
              { label: 'Toplam Kontrol', value: profile.total_inspections, icon: FileText },
              { label: 'Kazanç', value: `$${profile.earnings.toFixed(0)}`, icon: DollarSign },
              { label: 'Puan', value: profile.rating.toFixed(1), icon: Star },
              { label: 'Durum', value: profile.id_verified ? 'Onaylı' : 'Onay Bekliyor', icon: Shield },
            ].map((stat, i) => (
              <div key={i} className="bg-[#141414] border border-[#262626] rounded-2xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[#A3A3A3] text-sm">{stat.label}</p>
                    <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  </div>
                  <div className="w-12 h-12 bg-[#FFBF00]/10 rounded-xl flex items-center justify-center">
                    <stat.icon className="w-6 h-6 text-[#FFBF00]" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          {[
            { id: 'available', label: 'Mevcut İşler' },
            { id: 'my-jobs', label: 'İşlerim' },
            { id: 'map', label: 'Harita' },
          ].map(tab => (
            <button
              key={tab.id}
              data-testid={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === tab.id 
                  ? 'bg-[#FFBF00] text-[#0A0A0A]' 
                  : 'bg-[#141414] text-white hover:bg-[#1A1A1A]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Available Jobs */}
        {activeTab === 'available' && (
          <div className="bg-[#141414] border border-[#262626] rounded-2xl">
            <div className="p-6 border-b border-[#262626]">
              <h2 className="text-xl font-bold text-white">Mevcut Kontrol İşleri</h2>
            </div>
            
            {!profile?.id_verified ? (
              <div className="p-12 text-center">
                <Shield className="w-16 h-16 text-[#262626] mx-auto mb-4" />
                <p className="text-[#A3A3A3]">İşleri görmek için önce kimliğinizi onaylatın</p>
              </div>
            ) : availableJobs.length === 0 ? (
              <div className="p-12 text-center">
                <MapPin className="w-16 h-16 text-[#262626] mx-auto mb-4" />
                <p className="text-[#A3A3A3]">Yakınınızda mevcut iş yok</p>
              </div>
            ) : (
              <div className="divide-y divide-[#262626]">
                {availableJobs.map(job => (
                  <div 
                    key={job.id} 
                    className="p-6 hover:bg-[#1A1A1A] transition-colors cursor-pointer"
                    onClick={() => setSelectedJob(job)}
                    data-testid={`job-item-${job.id}`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-[#262626] rounded-xl flex items-center justify-center">
                          <Car className="w-6 h-6 text-[#FFBF00]" />
                        </div>
                        <div>
                          <p className="font-bold text-white">
                            {job.vehicle.year} {job.vehicle.make} {job.vehicle.model}
                          </p>
                          <p className="text-sm text-[#A3A3A3]">
                            {job.seller.city}, {job.seller.state} • {job.distance_miles} mil
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <p className="font-bold text-[#FFBF00] text-xl">${job.total_amount}</p>
                        <ChevronRight className="w-5 h-5 text-[#A3A3A3]" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* My Jobs */}
        {activeTab === 'my-jobs' && (
          <div className="bg-[#141414] border border-[#262626] rounded-2xl">
            <div className="p-6 border-b border-[#262626]">
              <h2 className="text-xl font-bold text-white">İşlerim</h2>
            </div>
            
            {myJobs.length === 0 ? (
              <div className="p-12 text-center">
                <FileText className="w-16 h-16 text-[#262626] mx-auto mb-4" />
                <p className="text-[#A3A3A3]">Henüz kabul ettiğiniz iş yok</p>
              </div>
            ) : (
              <div className="divide-y divide-[#262626]">
                {myJobs.map(job => (
                  <div 
                    key={job.id} 
                    className="p-6 hover:bg-[#1A1A1A] transition-colors cursor-pointer"
                    onClick={() => setSelectedJob(job)}
                    data-testid={`my-job-item-${job.id}`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-[#262626] rounded-xl flex items-center justify-center">
                          <Car className="w-6 h-6 text-[#FFBF00]" />
                        </div>
                        <div>
                          <p className="font-bold text-white">
                            {job.vehicle.year} {job.vehicle.make} {job.vehicle.model}
                          </p>
                          <p className="text-sm text-[#A3A3A3]">
                            {job.seller.city}, {job.seller.state}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          job.status === 'accepted' ? 'status-accepted' :
                          job.status === 'in_progress' ? 'status-in-progress' :
                          'status-completed'
                        }`}>
                          {job.status === 'accepted' ? 'Kabul Edildi' : 
                           job.status === 'in_progress' ? 'Devam Ediyor' : 'Tamamlandı'}
                        </span>
                        <p className="font-bold text-[#FFBF00]">${job.total_amount}</p>
                        <ChevronRight className="w-5 h-5 text-[#A3A3A3]" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Map View */}
        {activeTab === 'map' && (
          <div className="bg-[#141414] border border-[#262626] rounded-2xl overflow-hidden">
            <div className="h-[500px] map-container">
              <MapContainer 
                center={[41.8781, -87.6298]} 
                zoom={10} 
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                {availableJobs.map(job => (
                  <Marker 
                    key={job.id}
                    position={[job.seller.lat, job.seller.lng]}
                    icon={createCustomIcon()}
                    eventHandlers={{
                      click: () => setSelectedJob(job)
                    }}
                  >
                    <Popup>
                      <div className="text-black">
                        <p className="font-bold">{job.vehicle.year} {job.vehicle.make} {job.vehicle.model}</p>
                        <p className="text-sm">{job.seller.city}, {job.seller.state}</p>
                        <p className="font-bold text-amber-600">${job.total_amount}</p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>
        )}

        {/* Job Detail Modal */}
        {selectedJob && (
          <JobDetailModal 
            job={selectedJob} 
            onClose={() => { setSelectedJob(null); fetchMyJobs(); fetchAvailableJobs(); }}
            onAccept={handleAcceptJob}
            isInspector={true}
            userId={user.id}
          />
        )}

        {/* Verify ID Modal */}
        {showVerifyModal && (
          <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
            <div className="bg-[#141414] border border-[#262626] rounded-2xl w-full max-w-md p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Kimlik Doğrulama</h2>
              <p className="text-[#A3A3A3] mb-6">
                Kontrolcü olarak iş alabilmek için kimliğinizi doğrulamanız gerekmektedir.
              </p>
              <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-4 mb-6">
                <p className="text-sm text-[#A3A3A3]">
                  Gerçek uygulamada burada kimlik belgesi yükleme ve doğrulama süreci olacaktır.
                </p>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowVerifyModal(false)}
                  className="flex-1 py-3 border border-[#262626] text-white rounded-xl hover:bg-[#1A1A1A]"
                >
                  İptal
                </button>
                <button
                  data-testid="confirm-verify-btn"
                  onClick={handleVerifyId}
                  className="flex-1 py-3 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147]"
                >
                  Onayla (Demo)
                </button>
              </div>
            </div>
          </div>
        )}

        {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      </div>
    </div>
  );
};

// Job Detail Modal (for Inspector)
const JobDetailModal = ({ job, onClose, onAccept, isInspector, userId }) => {
  const [securityCode, setSecurityCode] = useState(['', '', '', '', '', '']);
  const [codeVerified, setCodeVerified] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(null);
  const [notes, setNotes] = useState('');
  const [recommendation, setRecommendation] = useState('buy');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const steps = [
    { name: 'exterior_front', label: 'Ön Görünüm', desc: 'Hood, ızgara, farlar, tampon' },
    { name: 'exterior_sides', label: 'Yan Görünüm', desc: 'Kapılar, paneller, aynalar, jantlar' },
    { name: 'exterior_rear', label: 'Arka Görünüm', desc: 'Bagaj, stop lambaları, tampon' },
    { name: 'interior', label: 'İç Mekan', desc: 'Gösterge paneli, koltuklar, konsol' },
    { name: 'engine', label: 'Motor', desc: 'Motor, sıvılar, kayışlar, hortumlar' },
    { name: 'undercarriage', label: 'Alt Kısım', desc: 'Şase, süspansiyon, egzoz' },
    { name: 'vin_verification', label: 'VIN Doğrulama', desc: 'VIN plakası ve belgeler' },
    { name: 'test_drive', label: 'Test Sürüşü', desc: 'Test sürüşü notları' },
  ];

  useEffect(() => {
    if (job.status === 'in_progress') {
      setCodeVerified(true);
      fetchProgress();
    }
  }, [job]);

  const fetchProgress = async () => {
    try {
      const res = await axios.get(`${API}/inspections/${job.id}/progress`);
      setProgress(res.data);
      setCurrentStep(res.data.current_step || 0);
    } catch (e) {
      console.error('Error fetching progress:', e);
    }
  };

  const handleCodeChange = (index, value) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newCode = [...securityCode];
      newCode[index] = value;
      setSecurityCode(newCode);
      
      if (value && index < 5) {
        document.getElementById(`otp-${index + 1}`)?.focus();
      }
    }
  };

  const handleVerifyCode = async () => {
    const code = securityCode.join('');
    if (code.length !== 6) return;

    setLoading(true);
    try {
      await axios.post(`${API}/inspections/${job.id}/verify-code?code=${code}&inspector_id=${userId}`);
      setCodeVerified(true);
      fetchProgress();
      setToast({ message: 'Kod doğrulandı! Kontrole başlayabilirsiniz.', type: 'success' });
    } catch (e) {
      setToast({ message: 'Geçersiz kod', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteStep = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/inspections/${job.id}/complete-step?step_name=${steps[currentStep].name}&notes=${notes}`);
      setNotes('');
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      }
      fetchProgress();
      setToast({ message: 'Adım tamamlandı!', type: 'success' });
    } catch (e) {
      setToast({ message: 'Hata oluştu', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReport = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/inspections/${job.id}/submit-report?inspector_id=${userId}`, {
        inspection_id: job.id,
        steps: progress?.steps || [],
        overall_notes: notes,
        recommendation
      });
      setToast({ message: 'Rapor gönderildi! Ödemeniz yolda.', type: 'success' });
      setTimeout(onClose, 2000);
    } catch (e) {
      setToast({ message: 'Hata oluştu', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#141414] border border-[#262626] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-[#262626] flex items-center justify-between sticky top-0 bg-[#141414] z-10">
          <h2 className="text-xl font-bold text-white">
            {job.vehicle.year} {job.vehicle.make} {job.vehicle.model}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-[#262626] rounded-full">
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <div className="p-6">
          {/* Job Info */}
          <div className="bg-[#0A0A0A] border border-[#262626] rounded-xl p-6 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[#A3A3A3] text-sm">Konum</p>
                <p className="text-white font-medium">{job.seller.city}, {job.seller.state}</p>
              </div>
              <div>
                <p className="text-[#A3A3A3] text-sm">Paket</p>
                <p className="text-white font-medium capitalize">{job.package_type}</p>
              </div>
              <div>
                <p className="text-[#A3A3A3] text-sm">Kazanç</p>
                <p className="text-[#FFBF00] font-bold text-xl">${job.total_amount}</p>
              </div>
              <div>
                <p className="text-[#A3A3A3] text-sm">Satıcı</p>
                <p className="text-white font-medium">{job.seller.name}</p>
              </div>
            </div>
          </div>

          {/* Pending - Accept Button */}
          {job.status === 'pending' && isInspector && (
            <button
              data-testid="accept-job-btn"
              onClick={() => onAccept(job.id)}
              className="w-full py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active"
            >
              İşi Kabul Et
            </button>
          )}

          {/* Accepted - Security Code Entry */}
          {job.status === 'accepted' && !codeVerified && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-bold text-white mb-2">Güvenlik Kodunu Girin</h3>
                <p className="text-[#A3A3A3] text-sm">
                  Satıcıdan aldığınız 6 haneli kodu girin
                </p>
              </div>

              <div className="flex justify-center gap-3">
                {securityCode.map((digit, i) => (
                  <input
                    key={i}
                    id={`otp-${i}`}
                    data-testid={`otp-input-${i}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleCodeChange(i, e.target.value)}
                    className="otp-input"
                  />
                ))}
              </div>

              <button
                data-testid="verify-code-btn"
                onClick={handleVerifyCode}
                disabled={securityCode.join('').length !== 6 || loading}
                className="w-full py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active disabled:opacity-50"
              >
                {loading ? 'Doğrulanıyor...' : 'Kodu Doğrula'}
              </button>
            </div>
          )}

          {/* In Progress - Inspection Steps */}
          {(job.status === 'in_progress' || codeVerified) && currentStep < steps.length && (
            <div className="space-y-6">
              {/* Progress Bar */}
              <div className="flex gap-1">
                {steps.map((_, i) => (
                  <div 
                    key={i} 
                    className={`h-2 flex-1 rounded-full ${
                      i < currentStep ? 'bg-[#34C759]' : 
                      i === currentStep ? 'bg-[#FFBF00]' : 'bg-[#262626]'
                    }`}
                  />
                ))}
              </div>

              <div className="text-center">
                <p className="overline mb-2">Adım {currentStep + 1}/{steps.length}</p>
                <h3 className="text-xl font-bold text-white">{steps[currentStep].label}</h3>
                <p className="text-[#A3A3A3]">{steps[currentStep].desc}</p>
              </div>

              {/* Photo Upload Placeholder */}
              <div className="border-2 border-dashed border-[#262626] rounded-xl p-8 text-center">
                <Camera className="w-12 h-12 text-[#A3A3A3] mx-auto mb-4" />
                <p className="text-[#A3A3A3] mb-4">Fotoğraf çekin veya yükleyin</p>
                <button className="px-6 py-3 bg-[#262626] text-white rounded-xl hover:bg-[#363636]">
                  Fotoğraf Ekle
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Notlar</label>
                <textarea
                  data-testid="step-notes-input"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Bu adım hakkında notlarınız..."
                  className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white h-24 resize-none"
                />
              </div>

              <button
                data-testid="complete-step-btn"
                onClick={handleCompleteStep}
                disabled={loading}
                className="w-full py-4 bg-[#FFBF00] text-[#0A0A0A] font-bold rounded-xl hover:bg-[#FFD147] transition-colors btn-active disabled:opacity-50"
              >
                {loading ? 'Kaydediliyor...' : currentStep < steps.length - 1 ? 'Sonraki Adım' : 'Adımı Tamamla'}
              </button>
            </div>
          )}

          {/* Submit Report */}
          {(job.status === 'in_progress' || codeVerified) && currentStep >= steps.length - 1 && progress?.steps?.every(s => s.completed) && (
            <div className="space-y-6 mt-6 pt-6 border-t border-[#262626]">
              <h3 className="text-lg font-bold text-white">Raporu Tamamla</h3>

              <div>
                <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Öneri</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'buy', label: 'Alınabilir', color: 'green' },
                    { id: 'caution', label: 'Dikkatli Ol', color: 'yellow' },
                    { id: 'avoid', label: 'Kaçın', color: 'red' },
                  ].map(rec => (
                    <button
                      key={rec.id}
                      data-testid={`rec-${rec.id}`}
                      onClick={() => setRecommendation(rec.id)}
                      className={`py-3 rounded-xl border-2 font-medium transition-all ${
                        recommendation === rec.id 
                          ? `border-${rec.color}-500 bg-${rec.color}-500/20 text-${rec.color}-400` 
                          : 'border-[#262626] text-[#A3A3A3]'
                      }`}
                    >
                      {rec.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#A3A3A3] mb-2">Genel Değerlendirme</label>
                <textarea
                  data-testid="overall-notes-input"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Araç hakkında genel değerlendirmeniz..."
                  className="w-full px-4 py-3 bg-[#0A0A0A] border-2 border-[#262626] rounded-xl text-white h-32 resize-none"
                />
              </div>

              <button
                data-testid="submit-report-btn"
                onClick={handleSubmitReport}
                disabled={loading}
                className="w-full py-4 bg-[#34C759] text-white font-bold rounded-xl hover:bg-[#2DB84D] transition-colors btn-active disabled:opacity-50"
              >
                {loading ? 'Gönderiliyor...' : 'Raporu Gönder'}
              </button>
            </div>
          )}
        </div>

        {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children, allowedType }) => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (allowedType && user.user_type !== allowedType) {
    return <Navigate to={user.user_type === 'buyer' ? '/buyer' : '/inspector'} />;
  }

  return children;
};

// Main App
function App() {
  return (
    <AuthProvider>
      <div className="App bg-[#0A0A0A] min-h-screen">
        <BrowserRouter>
          <Header />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route 
              path="/buyer" 
              element={
                <ProtectedRoute allowedType="buyer">
                  <BuyerDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/inspector" 
              element={
                <ProtectedRoute allowedType="inspector">
                  <InspectorDashboard />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;
