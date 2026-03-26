import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { inspectionsApi, notificationsApi } from '../services/api';
import { t } from '../i18n';
import { COLORS, STATUS_COLORS, APP_CONFIG } from '../config';

// Buyer Dashboard
export const BuyerDashboard = ({ navigation }) => {
  const { user } = useAuth();
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchInspections = async () => {
    try {
      const data = await inspectionsApi.getBuyerInspections(user.id);
      setInspections(data);
    } catch (e) {
      console.error('Error fetching inspections:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchInspections();
  }, []);

  const getStatusStyle = (status) => STATUS_COLORS[status] || STATUS_COLORS.pending;
  
  const getStatusText = (status) => {
    const texts = {
      pending: t('activeInspections'),
      accepted: t('activeInspections'),
      in_progress: t('activeInspections'),
      completed: t('completedInspections'),
    };
    return texts[status] || status;
  };

  const stats = {
    total: inspections.length,
    active: inspections.filter(i => ['pending', 'accepted', 'in_progress'].includes(i.status)).length,
    completed: inspections.filter(i => i.status === 'completed').length,
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>{t('buyerDashboard')}</Text>
            <Text style={styles.userName}>{user.full_name}</Text>
          </View>
          <TouchableOpacity
            style={styles.newButton}
            onPress={() => navigation.navigate('NewInspection')}
          >
            <Ionicons name="add" size={24} color={COLORS.background} />
          </TouchableOpacity>
        </View>

        {/* Stats */}
        <View style={styles.statsRow}>
          {[
            { label: t('myRequests'), value: stats.total, icon: 'document-text' },
            { label: t('activeInspections'), value: stats.active, icon: 'time' },
            { label: t('completedInspections'), value: stats.completed, icon: 'checkmark-circle' },
          ].map((stat, i) => (
            <View key={i} style={styles.statCard}>
              <Ionicons name={stat.icon} size={24} color={COLORS.primary} />
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
            </View>
          ))}
        </View>

        {/* Inspections List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('myRequests')}</Text>
          
          {inspections.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="car-sport-outline" size={64} color={COLORS.border} />
              <Text style={styles.emptyText}>{t('noInspections')}</Text>
              <TouchableOpacity
                style={styles.emptyButton}
                onPress={() => navigation.navigate('NewInspection')}
              >
                <Text style={styles.emptyButtonText}>{t('createFirst')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            inspections.map((inspection) => (
              <TouchableOpacity
                key={inspection.id}
                style={styles.inspectionCard}
                onPress={() => navigation.navigate('InspectionDetail', { inspection })}
              >
                <View style={styles.inspectionHeader}>
                  <View style={styles.carIcon}>
                    <Ionicons name="car-sport" size={24} color={COLORS.primary} />
                  </View>
                  <View style={styles.inspectionInfo}>
                    <Text style={styles.vehicleName}>
                      {inspection.vehicle.year} {inspection.vehicle.make} {inspection.vehicle.model}
                    </Text>
                    <Text style={styles.locationText}>
                      {inspection.seller.city}, {inspection.seller.state}
                    </Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusStyle(inspection.status).bg }]}>
                    <Text style={[styles.statusText, { color: getStatusStyle(inspection.status).text }]}>
                      {getStatusText(inspection.status)}
                    </Text>
                  </View>
                </View>

                {['pending', 'accepted'].includes(inspection.status) && (
                  <View style={styles.securityCodeBox}>
                    <Ionicons name="key" size={16} color={COLORS.primary} />
                    <Text style={styles.securityCodeLabel}>{t('securityCode')}: </Text>
                    <Text style={styles.securityCode}>{inspection.security_code}</Text>
                  </View>
                )}

                <View style={styles.inspectionFooter}>
                  <Text style={styles.totalAmount}>${inspection.total_amount}</Text>
                  <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// Inspection Detail Screen
export const InspectionDetailScreen = ({ route, navigation }) => {
  const { inspection } = route.params;
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (inspection.status === 'completed') {
      fetchReport();
    }
  }, [inspection]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const data = await reportsApi.getByInspection(inspection.id);
      setReport(data);
    } catch (e) {
      console.error('Error fetching report:', e);
    } finally {
      setLoading(false);
    }
  };

  const getRecStyle = (rec) => {
    const styles = {
      buy: { bg: 'rgba(52, 199, 89, 0.2)', text: '#34C759' },
      caution: { bg: 'rgba(255, 159, 10, 0.2)', text: '#FF9F0A' },
      avoid: { bg: 'rgba(255, 69, 58, 0.2)', text: '#FF453A' },
    };
    return styles[rec] || styles.caution;
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>

        <Text style={styles.detailTitle}>
          {inspection.vehicle.year} {inspection.vehicle.make} {inspection.vehicle.model}
        </Text>

        {/* Vehicle Info */}
        <View style={styles.detailCard}>
          <Text style={styles.detailCardTitle}>{t('vehicleInfo')}</Text>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>{t('make')} / {t('model')}</Text>
            <Text style={styles.detailValue}>{inspection.vehicle.make} {inspection.vehicle.model}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>{t('year')} / {t('color')}</Text>
            <Text style={styles.detailValue}>{inspection.vehicle.year} - {inspection.vehicle.color}</Text>
          </View>
        </View>

        {/* Security Code */}
        {['pending', 'accepted'].includes(inspection.status) && (
          <View style={styles.securityCodeCard}>
            <Text style={styles.securityCodeTitle}>{t('securityCode')}</Text>
            <Text style={styles.securityCodeBig}>{inspection.security_code}</Text>
            <Text style={styles.securityCodeInfo}>{t('securityCodeInfo')}</Text>
          </View>
        )}

        {/* Inspector Info */}
        {inspection.inspector_name && (
          <View style={styles.detailCard}>
            <Text style={styles.detailCardTitle}>Inspector</Text>
            <View style={styles.inspectorRow}>
              <View style={styles.inspectorAvatar}>
                <Ionicons name="person" size={24} color={COLORS.primary} />
              </View>
              <View>
                <Text style={styles.inspectorName}>{inspection.inspector_name}</Text>
                <Text style={styles.inspectorLabel}>Inspector</Text>
              </View>
            </View>
          </View>
        )}

        {/* Report */}
        {report && (
          <View style={styles.detailCard}>
            <View style={styles.reportHeader}>
              <Text style={styles.detailCardTitle}>{t('inspectionReport')}</Text>
              <View style={[styles.recBadge, { backgroundColor: getRecStyle(report.recommendation).bg }]}>
                <Text style={[styles.recText, { color: getRecStyle(report.recommendation).text }]}>
                  {t(report.recommendation)}
                </Text>
              </View>
            </View>
            
            {report.overall_notes && (
              <View style={styles.notesBox}>
                <Text style={styles.notesTitle}>{t('overallNotes')}</Text>
                <Text style={styles.notesText}>{report.overall_notes}</Text>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

// Import reportsApi
import { reportsApi } from '../services/api';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: {
    fontSize: 14,
    color: COLORS.textMuted,
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 4,
  },
  newButton: {
    width: 48,
    height: 48,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 8,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textMuted,
    marginTop: 4,
    textAlign: 'center',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 16,
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: 16,
    marginBottom: 16,
  },
  emptyButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  emptyButtonText: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  inspectionCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  inspectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  carIcon: {
    width: 48,
    height: 48,
    backgroundColor: COLORS.elevated,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  inspectionInfo: {
    flex: 1,
  },
  vehicleName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  locationText: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  securityCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  securityCodeLabel: {
    fontSize: 13,
    color: COLORS.primary,
    marginLeft: 8,
  },
  securityCode: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text,
    letterSpacing: 2,
  },
  inspectionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  totalAmount: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.primary,
  },
  backButton: {
    marginBottom: 16,
  },
  detailTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 24,
  },
  detailCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  detailCardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 14,
    color: COLORS.textMuted,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  securityCodeCard: {
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 191, 0, 0.3)',
  },
  securityCodeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 12,
  },
  securityCodeBig: {
    fontSize: 36,
    fontWeight: '700',
    color: COLORS.text,
    letterSpacing: 8,
    marginBottom: 12,
  },
  securityCodeInfo: {
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
    lineHeight: 18,
  },
  inspectorRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  inspectorAvatar: {
    width: 48,
    height: 48,
    backgroundColor: COLORS.elevated,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  inspectorName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  inspectorLabel: {
    fontSize: 13,
    color: COLORS.textMuted,
  },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  recBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  recText: {
    fontSize: 12,
    fontWeight: '700',
  },
  notesBox: {
    backgroundColor: COLORS.elevated,
    borderRadius: 12,
    padding: 16,
  },
  notesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
  },
  notesText: {
    fontSize: 14,
    color: COLORS.textMuted,
    lineHeight: 20,
  },
});
