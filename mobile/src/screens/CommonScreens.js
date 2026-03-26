import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { notificationsApi } from '../services/api';
import { t, availableLanguages } from '../i18n';
import { COLORS } from '../config';

// Notifications Screen
export const NotificationsScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const data = await notificationsApi.get(user.id);
      setNotifications(data);
    } catch (e) {
      console.error('Error fetching notifications:', e);
    } finally {
      setRefreshing(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await notificationsApi.markRead(id);
      fetchNotifications();
    } catch (e) {
      console.error('Error marking notification as read:', e);
    }
  };

  const getIcon = (type) => {
    const icons = {
      new_job: 'briefcase',
      inspection_accepted: 'checkmark-circle',
      report_ready: 'document-text',
    };
    return icons[type] || 'notifications';
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{t('notifications')}</Text>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              fetchNotifications();
            }}
            tintColor={COLORS.primary}
          />
        }
      >
        {notifications.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="notifications-off-outline" size={48} color={COLORS.border} />
            <Text style={styles.emptyText}>{t('noNotifications')}</Text>
          </View>
        ) : (
          notifications.map((notif) => (
            <TouchableOpacity
              key={notif.id}
              style={[styles.notificationCard, !notif.read && styles.notificationUnread]}
              onPress={() => markAsRead(notif.id)}
            >
              <View style={styles.notificationIcon}>
                <Ionicons name={getIcon(notif.type)} size={24} color={COLORS.primary} />
              </View>
              <View style={styles.notificationContent}>
                <Text style={styles.notificationTitle}>{notif.title}</Text>
                <Text style={styles.notificationMessage}>{notif.message}</Text>
              </View>
              {!notif.read && <View style={styles.unreadDot} />}
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

// Settings Screen
export const SettingsScreen = ({ navigation }) => {
  const { user, logout, language, setLanguage } = useAuth();
  const [showLanguageModal, setShowLanguageModal] = useState(false);

  const handleLogout = () => {
    logout();
  };

  const menuItems = [
    { icon: 'person-outline', label: t('profile'), onPress: () => {} },
    { icon: 'language-outline', label: t('language'), value: availableLanguages.find(l => l.code === language)?.name, onPress: () => setShowLanguageModal(true) },
    { icon: 'help-circle-outline', label: t('support'), onPress: () => {} },
    { icon: 'document-text-outline', label: t('termsOfService'), onPress: () => {} },
    { icon: 'shield-outline', label: t('privacyPolicy'), onPress: () => {} },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{t('settings')}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.userAvatar}>
            <Ionicons name="person" size={32} color={COLORS.primary} />
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user.full_name}</Text>
            <Text style={styles.userEmail}>{user.email}</Text>
            <View style={styles.userTypeBadge}>
              <Text style={styles.userTypeText}>
                {user.user_type === 'buyer' ? t('buyer') : t('inspector')}
              </Text>
            </View>
          </View>
        </View>

        {/* Menu Items */}
        <View style={styles.menuSection}>
          {menuItems.map((item, i) => (
            <TouchableOpacity key={i} style={styles.menuItem} onPress={item.onPress}>
              <View style={styles.menuItemLeft}>
                <Ionicons name={item.icon} size={22} color={COLORS.textMuted} />
                <Text style={styles.menuItemLabel}>{item.label}</Text>
              </View>
              <View style={styles.menuItemRight}>
                {item.value && <Text style={styles.menuItemValue}>{item.value}</Text>}
                <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Version */}
        <Text style={styles.version}>{t('version')} 1.0.0</Text>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={22} color={COLORS.error} />
          <Text style={styles.logoutText}>{t('logout')}</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Language Modal */}
      {showLanguageModal && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{t('language')}</Text>
            {availableLanguages.map((lang) => (
              <TouchableOpacity
                key={lang.code}
                style={[styles.languageOption, language === lang.code && styles.languageOptionActive]}
                onPress={() => {
                  setLanguage(lang.code);
                  setShowLanguageModal(false);
                }}
              >
                <Text style={styles.languageFlag}>{lang.flag}</Text>
                <Text style={[styles.languageName, language === lang.code && styles.languageNameActive]}>
                  {lang.name}
                </Text>
                {language === lang.code && (
                  <Ionicons name="checkmark" size={20} color={COLORS.primary} />
                )}
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowLanguageModal(false)}
            >
              <Text style={styles.modalCloseText}>{t('cancel')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 100,
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: 16,
  },
  notificationCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  notificationUnread: {
    backgroundColor: COLORS.elevated,
  },
  notificationIcon: {
    width: 44,
    height: 44,
    backgroundColor: COLORS.background,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  notificationMessage: {
    fontSize: 13,
    color: COLORS.textMuted,
    lineHeight: 18,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
    marginLeft: 8,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  userAvatar: {
    width: 64,
    height: 64,
    backgroundColor: COLORS.elevated,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  userEmail: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  userTypeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginTop: 8,
  },
  userTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  menuSection: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 24,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuItemLabel: {
    fontSize: 15,
    color: COLORS.text,
  },
  menuItemRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  menuItemValue: {
    fontSize: 14,
    color: COLORS.textMuted,
  },
  version: {
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginBottom: 24,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.error,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: COLORS.card,
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 320,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 20,
    textAlign: 'center',
  },
  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: COLORS.elevated,
  },
  languageOptionActive: {
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  languageFlag: {
    fontSize: 24,
    marginRight: 12,
  },
  languageName: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  languageNameActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  modalCloseButton: {
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  modalCloseText: {
    fontSize: 16,
    color: COLORS.textMuted,
  },
});
