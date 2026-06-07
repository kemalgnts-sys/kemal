import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Dimensions,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, PROVIDER_DEFAULT } from 'react-native-maps';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { Camera } from 'expo-camera';
import { useAuth } from '../context/AuthContext';
import { inspectionsApi, inspectorApi } from '../services/api';
import { t } from '../i18n';
import { COLORS, STATUS_COLORS, APP_CONFIG } from '../config';

const { width, height } = Dimensions.get('window');

// Inspector Dashboard
export const InspectorDashboard = ({ navigation }) => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [availableJobs, setAvailableJobs] = useState([]);
  const [myJobs, setMyJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('available');
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [location, setLocation] = useState(null);
  const mapRef = useRef(null);

  useEffect(() => {
    getLocation();
    fetchProfile();
    fetchJobs();
  }, []);

  const getLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({});
        setLocation({
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
        });
      }
    } catch (e) {
      console.error('Error getting location:', e);
    }
  };

  const fetchProfile = async () => {
    try {
      const data = await inspectorApi.getProfile(user.id);
      setProfile(data);
    } catch (e) {
      console.error('Error fetching profile:', e);
    }
  };

  const fetchJobs = async () => {
    try {
      const lat = location?.latitude || APP_CONFIG.defaultLocation.latitude;
      const lng = location?.longitude || APP_CONFIG.defaultLocation.longitude;
      
      const [available, mine] = await Promise.all([
        inspectionsApi.getAvailable(lat, lng),
        inspectorApi.getJobs(user.id),
      ]);
      
      setAvailableJobs(available);
      setMyJobs(mine);
    } catch (e) {
      console.error('Error fetching jobs:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchProfile();
    fetchJobs();
  }, [location]);

  const handleVerifyId = async () => {
    try {
      await inspectorApi.verifyId(user.id);
      fetchProfile();
      setShowVerifyModal(false);
      Alert.alert(t('success'), 'ID verified successfully!');
    } catch (e) {
      Alert.alert(t('error'), 'Verification failed');
    }
  };

  const handleAcceptJob = async (job) => {
    try {
      await inspectionsApi.accept(job.id, user.id);
      Alert.alert(t('success'), 'Job accepted!');
      fetchJobs();
    } catch (e) {
      Alert.alert(t('error'), e.response?.data?.detail || 'Failed to accept job');
    }
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
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>{t('inspectorDashboard')}</Text>
          <Text style={styles.userName}>{user.full_name}</Text>
        </View>
        {profile && !profile.id_verified && (
          <TouchableOpacity style={styles.verifyButton} onPress={() => setShowVerifyModal(true)}>
            <Ionicons name="shield-checkmark" size={20} color={COLORS.background} />
            <Text style={styles.verifyButtonText}>{t('verifyId')}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Stats */}
      {profile && (
        <View style={styles.statsRow}>
          {[
            { label: t('totalInspections'), value: profile.total_inspections, icon: 'document-text' },
            { label: t('earnings'), value: `$${profile.earnings.toFixed(0)}`, icon: 'wallet' },
            { label: t('rating'), value: profile.rating.toFixed(1), icon: 'star' },
          ].map((stat, i) => (
            <View key={i} style={styles.statCard}>
              <Ionicons name={stat.icon} size={20} color={COLORS.primary} />
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        {[
          { id: 'available', label: t('availableJobs'), icon: 'list' },
          { id: 'my-jobs', label: t('myJobs'), icon: 'briefcase' },
          { id: 'map', label: t('mapView'), icon: 'map' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[styles.tab, activeTab === tab.id && styles.tabActive]}
            onPress={() => setActiveTab(tab.id)}
          >
            <Ionicons
              name={tab.icon}
              size={18}
              color={activeTab === tab.id ? COLORS.background : COLORS.textMuted}
            />
            <Text style={[styles.tabText, activeTab === tab.id && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {activeTab === 'map' ? (
        <View style={styles.mapContainer}>
          <MapView
            ref={mapRef}
            style={styles.map}
            initialRegion={{
              ...(location || APP_CONFIG.defaultLocation),
              latitudeDelta: 0.5,
              longitudeDelta: 0.5,
            }}
            userInterfaceStyle="dark"
          >
            {availableJobs.map((job) => (
              <Marker
                key={job.id}
                coordinate={{
                  latitude: job.seller.lat,
                  longitude: job.seller.lng,
                }}
                title={`${job.vehicle.year} ${job.vehicle.make} ${job.vehicle.model}`}
                description={`$${job.total_amount} - ${job.distance_miles} ${t('distance')}`}
                onCalloutPress={() => navigation.navigate('JobDetail', { job, onAccept: handleAcceptJob })}
              >
                <View style={styles.customMarker}>
                  <Ionicons name="car" size={16} color={COLORS.background} />
                </View>
              </Marker>
            ))}
          </MapView>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
        >
          {!profile?.id_verified ? (
            <View style={styles.verifyPrompt}>
              <Ionicons name="shield-outline" size={48} color={COLORS.border} />
              <Text style={styles.verifyPromptText}>{t('idPending')}</Text>
              <TouchableOpacity style={styles.verifyPromptButton} onPress={() => setShowVerifyModal(true)}>
                <Text style={styles.verifyPromptButtonText}>{t('verifyId')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {activeTab === 'available' && (
                availableJobs.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="location-outline" size={48} color={COLORS.border} />
                    <Text style={styles.emptyText}>{t('noJobs')}</Text>
                  </View>
                ) : (
                  availableJobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      onPress={() => navigation.navigate('JobDetail', { job, onAccept: handleAcceptJob })}
                      showAccept
                      onAccept={() => handleAcceptJob(job)}
                    />
                  ))
                )
              )}

              {activeTab === 'my-jobs' && (
                myJobs.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="briefcase-outline" size={48} color={COLORS.border} />
                    <Text style={styles.emptyText}>{t('noJobs')}</Text>
                  </View>
                ) : (
                  myJobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      onPress={() => navigation.navigate('JobDetail', { job, isMyJob: true })}
                      showStatus
                    />
                  ))
                )
              )}
            </>
          )}
        </ScrollView>
      )}

      {/* Verify ID Modal */}
      <Modal visible={showVerifyModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{t('verifyId')}</Text>
            <Text style={styles.modalText}>
              ID verification is required to accept jobs. In a real app, this would involve uploading government ID.
            </Text>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButtonSecondary}
                onPress={() => setShowVerifyModal(false)}
              >
                <Text style={styles.modalButtonSecondaryText}>{t('cancel')}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalButtonPrimary} onPress={handleVerifyId}>
                <Text style={styles.modalButtonPrimaryText}>{t('confirm')} (Demo)</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

// Job Card Component
const JobCard = ({ job, onPress, showAccept, onAccept, showStatus }) => {
  const getStatusStyle = (status) => STATUS_COLORS[status] || STATUS_COLORS.pending;

  return (
    <TouchableOpacity style={styles.jobCard} onPress={onPress}>
      <View style={styles.jobHeader}>
        <View style={styles.carIcon}>
          <Ionicons name="car-sport" size={24} color={COLORS.primary} />
        </View>
        <View style={styles.jobInfo}>
          <Text style={styles.vehicleName}>
            {job.vehicle.year} {job.vehicle.make} {job.vehicle.model}
          </Text>
          <Text style={styles.locationText}>
            {job.seller.city}, {job.seller.state}
            {job.distance_miles && ` • ${job.distance_miles} ${t('distance')}`}
          </Text>
        </View>
        <Text style={styles.jobAmount}>${job.total_amount}</Text>
      </View>

      {showStatus && (
        <View style={[styles.statusBadge, { backgroundColor: getStatusStyle(job.status).bg, alignSelf: 'flex-start', marginTop: 12 }]}>
          <Text style={[styles.statusText, { color: getStatusStyle(job.status).text }]}>
            {job.status}
          </Text>
        </View>
      )}

      {showAccept && (
        <TouchableOpacity style={styles.acceptButton} onPress={onAccept}>
          <Text style={styles.acceptButtonText}>{t('acceptJob')}</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
};

// Job Detail Screen
export const JobDetailScreen = ({ route, navigation }) => {
  const { job, onAccept, isMyJob } = route.params;
  const { user } = useAuth();
  const [securityCode, setSecurityCode] = useState(['', '', '', '', '', '']);
  const [codeVerified, setCodeVerified] = useState(job.status === 'in_progress');
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(null);
  const [notes, setNotes] = useState('');
  const [recommendation, setRecommendation] = useState('buy');
  const [loading, setLoading] = useState(false);
  const [photos, setPhotos] = useState([]);
  const codeInputRefs = useRef([]);

  const steps = [
    { name: 'exterior_front', title: t('exteriorFront'), desc: t('exteriorFrontDesc') },
    { name: 'exterior_sides', title: t('exteriorSides'), desc: t('exteriorSidesDesc') },
    { name: 'exterior_rear', title: t('exteriorRear'), desc: t('exteriorRearDesc') },
    { name: 'interior', title: t('interior'), desc: t('interiorDesc') },
    { name: 'engine', title: t('engine'), desc: t('engineDesc') },
    { name: 'undercarriage', title: t('undercarriage'), desc: t('undercarriageDesc') },
    { name: 'vin_verification', title: t('vinVerification'), desc: t('vinVerificationDesc') },
    { name: 'test_drive', title: t('testDrive'), desc: t('testDriveDesc') },
  ];

  useEffect(() => {
    if (job.status === 'in_progress') {
      fetchProgress();
    }
  }, [job]);

  const fetchProgress = async () => {
    try {
      const data = await inspectionsApi.getProgress(job.id);
      setProgress(data);
      setCurrentStep(data.current_step || 0);
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
        codeInputRefs.current[index + 1]?.focus();
      }
    }
  };

  const handleVerifyCode = async () => {
    const code = securityCode.join('');
    if (code.length !== 6) return;

    setLoading(true);
    try {
      await inspectionsApi.verifyCode(job.id, code, user.id);
      setCodeVerified(true);
      fetchProgress();
      Alert.alert(t('success'), 'Code verified! You can start the inspection.');
    } catch (e) {
      Alert.alert(t('error'), t('invalidCode'));
    } finally {
      setLoading(false);
    }
  };

  const handleTakePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(t('error'), 'Camera permission is required');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setPhotos([...photos, result.assets[0].uri]);
      
      // Upload photo
      try {
        await inspectionsApi.uploadPhoto(job.id, steps[currentStep].name, result.assets[0].uri);
      } catch (e) {
        console.error('Error uploading photo:', e);
      }
    }
  };

  const handleCompleteStep = async () => {
    setLoading(true);
    try {
      await inspectionsApi.completeStep(job.id, steps[currentStep].name, notes);
      setNotes('');
      setPhotos([]);
      
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      }
      fetchProgress();
    } catch (e) {
      Alert.alert(t('error'), 'Failed to complete step');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReport = async () => {
    setLoading(true);
    try {
      await inspectionsApi.submitReport(job.id, user.id, {
        inspection_id: job.id,
        steps: progress?.steps || [],
        overall_notes: notes,
        recommendation,
      });
      Alert.alert(t('success'), 'Report submitted! Payment will be processed.');
      navigation.goBack();
    } catch (e) {
      Alert.alert(t('error'), 'Failed to submit report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>

        <Text style={styles.detailTitle}>
          {job.vehicle.year} {job.vehicle.make} {job.vehicle.model}
        </Text>

        {/* Job Info */}
        <View style={styles.jobInfoCard}>
          <View style={styles.jobInfoRow}>
            <Text style={styles.jobInfoLabel}>{t('city')}</Text>
            <Text style={styles.jobInfoValue}>{job.seller.city}, {job.seller.state}</Text>
          </View>
          <View style={styles.jobInfoRow}>
            <Text style={styles.jobInfoLabel}>{t('earnings')}</Text>
            <Text style={styles.jobInfoValueHighlight}>${job.total_amount}</Text>
          </View>
        </View>

        {/* Pending - Accept Button */}
        {job.status === 'pending' && !isMyJob && (
          <TouchableOpacity
            style={styles.acceptButtonLarge}
            onPress={() => {
              onAccept && onAccept(job);
              navigation.goBack();
            }}
          >
            <Text style={styles.acceptButtonLargeText}>{t('acceptJob')}</Text>
          </TouchableOpacity>
        )}

        {/* Accepted - Security Code Entry */}
        {job.status === 'accepted' && !codeVerified && (
          <View style={styles.codeSection}>
            <Text style={styles.codeSectionTitle}>{t('enterCode')}</Text>
            <Text style={styles.codeSectionSubtitle}>{t('enterCodeDesc')}</Text>

            <View style={styles.codeInputContainer}>
              {securityCode.map((digit, i) => (
                <TextInput
                  key={i}
                  ref={(ref) => (codeInputRefs.current[i] = ref)}
                  style={styles.codeInput}
                  value={digit}
                  onChangeText={(v) => handleCodeChange(i, v)}
                  keyboardType="numeric"
                  maxLength={1}
                />
              ))}
            </View>

            <TouchableOpacity
              style={[styles.verifyCodeButton, securityCode.join('').length !== 6 && styles.buttonDisabled]}
              onPress={handleVerifyCode}
              disabled={securityCode.join('').length !== 6 || loading}
            >
              {loading ? (
                <ActivityIndicator color={COLORS.background} />
              ) : (
                <Text style={styles.verifyCodeButtonText}>{t('verifyCode')}</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* In Progress - Inspection Steps */}
        {(job.status === 'in_progress' || codeVerified) && currentStep < steps.length && (
          <View style={styles.stepsSection}>
            {/* Progress Bar */}
            <View style={styles.progressBar}>
              {steps.map((_, i) => (
                <View
                  key={i}
                  style={[
                    styles.progressSegment,
                    i < currentStep && styles.progressSegmentComplete,
                    i === currentStep && styles.progressSegmentActive,
                  ]}
                />
              ))}
            </View>

            <Text style={styles.stepCounter}>
              {t('inspectionSteps')}: {currentStep + 1}/{steps.length}
            </Text>
            <Text style={styles.stepTitle}>{steps[currentStep].title}</Text>
            <Text style={styles.stepDesc}>{steps[currentStep].desc}</Text>

            {/* Photos */}
            <View style={styles.photosContainer}>
              {photos.map((uri, i) => (
                <Image key={i} source={{ uri }} style={styles.photoThumb} />
              ))}
              <TouchableOpacity style={styles.addPhotoButton} onPress={handleTakePhoto}>
                <Ionicons name="camera" size={32} color={COLORS.primary} />
                <Text style={styles.addPhotoText}>{t('takePhoto')}</Text>
              </TouchableOpacity>
            </View>

            {/* Notes */}
            <TextInput
              style={styles.notesInput}
              value={notes}
              onChangeText={setNotes}
              placeholder={t('addNotes')}
              placeholderTextColor={COLORS.textMuted}
              multiline
            />

            <TouchableOpacity
              style={[styles.completeStepButton, loading && styles.buttonDisabled]}
              onPress={handleCompleteStep}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={COLORS.background} />
              ) : (
                <Text style={styles.completeStepButtonText}>
                  {currentStep < steps.length - 1 ? t('nextStep') : t('completeStep')}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Submit Report */}
        {(job.status === 'in_progress' || codeVerified) && currentStep >= steps.length - 1 && progress?.steps?.every((s) => s.completed) && (
          <View style={styles.reportSection}>
            <Text style={styles.reportTitle}>{t('submitReport')}</Text>

            <Text style={styles.recLabel}>{t('recommendation')}</Text>
            <View style={styles.recOptions}>
              {['buy', 'caution', 'avoid'].map((rec) => (
                <TouchableOpacity
                  key={rec}
                  style={[styles.recOption, recommendation === rec && styles.recOptionActive]}
                  onPress={() => setRecommendation(rec)}
                >
                  <Text style={[styles.recOptionText, recommendation === rec && styles.recOptionTextActive]}>
                    {t(rec)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TextInput
              style={styles.notesInputLarge}
              value={notes}
              onChangeText={setNotes}
              placeholder={t('overallNotes')}
              placeholderTextColor={COLORS.textMuted}
              multiline
            />

            <TouchableOpacity
              style={[styles.submitReportButton, loading && styles.buttonDisabled]}
              onPress={handleSubmitReport}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={COLORS.text} />
              ) : (
                <Text style={styles.submitReportButtonText}>{t('submitReport')}</Text>
              )}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

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
    padding: 20,
    paddingBottom: 0,
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
  verifyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  verifyButtonText: {
    color: COLORS.background,
    fontWeight: '600',
    fontSize: 13,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
    padding: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 6,
  },
  statLabel: {
    fontSize: 10,
    color: COLORS.textMuted,
    marginTop: 2,
    textAlign: 'center',
  },
  tabsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 16,
    gap: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    backgroundColor: COLORS.card,
    borderRadius: 10,
  },
  tabActive: {
    backgroundColor: COLORS.primary,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  tabTextActive: {
    color: COLORS.background,
  },
  mapContainer: {
    flex: 1,
    margin: 20,
    marginTop: 0,
    borderRadius: 16,
    overflow: 'hidden',
  },
  map: {
    width: '100%',
    height: height * 0.5,
  },
  customMarker: {
    width: 32,
    height: 32,
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: COLORS.background,
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
  verifyPrompt: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    marginHorizontal: 20,
  },
  verifyPromptText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: 16,
    marginBottom: 16,
  },
  verifyPromptButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 10,
  },
  verifyPromptButtonText: {
    color: COLORS.background,
    fontWeight: '600',
  },
  jobCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jobHeader: {
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
  jobInfo: {
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
  jobAmount: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.primary,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  acceptButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 16,
  },
  acceptButtonText: {
    color: COLORS.background,
    fontWeight: '700',
    fontSize: 14,
  },
  modalOverlay: {
    flex: 1,
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
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 12,
  },
  modalText: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 24,
    lineHeight: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButtonSecondary: {
    flex: 1,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    alignItems: 'center',
  },
  modalButtonSecondaryText: {
    color: COLORS.text,
    fontWeight: '600',
  },
  modalButtonPrimary: {
    flex: 1,
    padding: 14,
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    alignItems: 'center',
  },
  modalButtonPrimaryText: {
    color: COLORS.background,
    fontWeight: '600',
  },
  backButton: {
    marginBottom: 16,
  },
  detailTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 20,
  },
  jobInfoCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jobInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  jobInfoLabel: {
    fontSize: 14,
    color: COLORS.textMuted,
  },
  jobInfoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  jobInfoValueHighlight: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
  },
  acceptButtonLarge: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  acceptButtonLargeText: {
    color: COLORS.background,
    fontWeight: '700',
    fontSize: 16,
  },
  codeSection: {
    alignItems: 'center',
    padding: 24,
  },
  codeSectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 8,
  },
  codeSectionSubtitle: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 24,
  },
  codeInputContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  codeInput: {
    width: 48,
    height: 56,
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 12,
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
  },
  verifyCodeButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 48,
  },
  verifyCodeButtonText: {
    color: COLORS.background,
    fontWeight: '700',
    fontSize: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  stepsSection: {
    marginTop: 20,
  },
  progressBar: {
    flexDirection: 'row',
    gap: 4,
    marginBottom: 20,
  },
  progressSegment: {
    flex: 1,
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
  },
  progressSegmentComplete: {
    backgroundColor: COLORS.success,
  },
  progressSegmentActive: {
    backgroundColor: COLORS.primary,
  },
  stepCounter: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 8,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 8,
  },
  stepDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 24,
  },
  photosContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  photoThumb: {
    width: 80,
    height: 80,
    borderRadius: 12,
  },
  addPhotoButton: {
    width: 80,
    height: 80,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
  },
  addPhotoText: {
    fontSize: 10,
    color: COLORS.textMuted,
    marginTop: 4,
  },
  notesInput: {
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: COLORS.text,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 20,
  },
  completeStepButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  completeStepButtonText: {
    color: COLORS.background,
    fontWeight: '700',
    fontSize: 16,
  },
  reportSection: {
    marginTop: 32,
    padding: 20,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  reportTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 20,
  },
  recLabel: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 12,
  },
  recOptions: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  recOption: {
    flex: 1,
    padding: 12,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 10,
    alignItems: 'center',
  },
  recOptionActive: {
    borderColor: COLORS.primary,
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
  },
  recOptionText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  recOptionTextActive: {
    color: COLORS.primary,
  },
  notesInputLarge: {
    backgroundColor: COLORS.elevated,
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: COLORS.text,
    minHeight: 120,
    textAlignVertical: 'top',
    marginBottom: 20,
  },
  submitReportButton: {
    backgroundColor: COLORS.success,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  submitReportButtonText: {
    color: COLORS.text,
    fontWeight: '700',
    fontSize: 16,
  },
});
