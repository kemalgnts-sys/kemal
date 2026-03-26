// API Configuration
// Replace with your production URL when deploying
export const API_BASE_URL = 'https://turkce-chat-app-2.preview.emergentagent.com/api';

// App Configuration
export const APP_CONFIG = {
  name: 'AutoCheck',
  version: '1.0.0',
  
  // Inspection packages
  packages: {
    basic: { price: 100, name: 'Basic' },
    premium: { price: 250, name: 'Premium' },
    professional: { price: 300, name: 'Professional' },
  },
  
  // Tip options
  tipOptions: [0, 10, 20, 30],
  
  // Inspector search radius (miles)
  defaultSearchRadius: 50,
  maxSearchRadius: 100,
  
  // Map defaults (Chicago)
  defaultLocation: {
    latitude: 41.8781,
    longitude: -87.6298,
    latitudeDelta: 0.5,
    longitudeDelta: 0.5,
  },
};

// Colors - Amber & Black theme
export const COLORS = {
  primary: '#FFBF00',
  primaryHover: '#FFD147',
  background: '#0A0A0A',
  card: '#141414',
  elevated: '#1A1A1A',
  border: '#262626',
  text: '#FFFFFF',
  textMuted: '#A3A3A3',
  success: '#34C759',
  warning: '#FF9F0A',
  error: '#FF453A',
  info: '#0A84FF',
};

// Status colors
export const STATUS_COLORS = {
  pending: { bg: 'rgba(255, 159, 10, 0.2)', text: '#FF9F0A' },
  accepted: { bg: 'rgba(10, 132, 255, 0.2)', text: '#0A84FF' },
  in_progress: { bg: 'rgba(255, 191, 0, 0.2)', text: '#FFBF00' },
  completed: { bg: 'rgba(52, 199, 89, 0.2)', text: '#34C759' },
};

// Recommendation colors
export const REC_COLORS = {
  buy: { bg: 'rgba(52, 199, 89, 0.2)', text: '#34C759' },
  caution: { bg: 'rgba(255, 159, 10, 0.2)', text: '#FF9F0A' },
  avoid: { bg: 'rgba(255, 69, 58, 0.2)', text: '#FF453A' },
};
