import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { inspectionsApi } from '../services/api';
import { t } from '../i18n';
import { COLORS, APP_CONFIG } from '../config';

export const NewInspectionScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    vehicle: { make: '', model: '', year: '2020', vin: '', color: '', mileage: '' },
    seller: { name: '', phone: '', address: '', city: '', state: '', zip_code: '', lat: 41.8781, lng: -87.6298 },
    package_type: 'basic',
    tip_amount: 0,
    notes: '',
  });

  const packages = [
    { id: 'basic', name: t('basic'), price: 100, desc: t('basicDesc'), features: ['15 photos', 'Exterior check', 'Interior check', 'Test drive'] },
    { id: 'premium', name: t('premium'), price: 250, desc: t('premiumDesc'), features: ['30 photos', 'Video', 'Engine detail', 'Undercarriage'] },
    { id: 'professional', name: t('professional'), price: 300, desc: t('professionalDesc'), features: ['50+ photos', 'OBD-II scan', 'Paint depth', 'Video call'], isPro: true },
  ];

  const selectedPackage = packages.find(p => p.id === formData.package_type);
  const totalAmount = (selectedPackage?.price || 0) + formData.tip_amount;

  const updateVehicle = (key, value) => {
    setFormData({ ...formData, vehicle: { ...formData.vehicle, [key]: value } });
  };

  const updateSeller = (key, value) => {
    setFormData({ ...formData, seller: { ...formData.seller, [key]: value } });
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const data = {
        ...formData,
        vehicle: {
          ...formData.vehicle,
          year: parseInt(formData.vehicle.year),
          mileage: formData.vehicle.mileage ? parseInt(formData.vehicle.mileage) : null,
        },
      };
      await inspectionsApi.create(user.id, data);
      Alert.alert(t('success'), 'Inspection request created!', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (e) {
      Alert.alert(t('error'), e.response?.data?.detail || 'Failed to create request');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    if (step === 1) {
      return formData.vehicle.make && formData.vehicle.model && formData.vehicle.year && formData.vehicle.color;
    }
    if (step === 2) {
      return formData.seller.name && formData.seller.phone && formData.seller.address && formData.seller.city && formData.seller.state && formData.seller.zip_code;
    }
    return true;
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView 
        style={styles.keyboardView} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Ionicons name="close" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('newInspection')}</Text>
          <View style={{ width: 28 }} />
        </View>

        {/* Progress */}
        <View style={styles.progressContainer}>
          {[1, 2, 3, 4].map((s) => (
            <View
              key={s}
              style={[
                styles.progressDot,
                s <= step && styles.progressDotActive,
              ]}
            />
          ))}
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Step 1: Vehicle Info */}
          {step === 1 && (
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>{t('vehicleInfo')}</Text>
              
              <View style={styles.row}>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('make')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.vehicle.make}
                    onChangeText={(v) => updateVehicle('make', v)}
                    placeholder="Toyota"
                    placeholderTextColor={COLORS.textMuted}
                  />
                </View>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('model')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.vehicle.model}
                    onChangeText={(v) => updateVehicle('model', v)}
                    placeholder="Camry"
                    placeholderTextColor={COLORS.textMuted}
                  />
                </View>
              </View>

              <View style={styles.row}>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('year')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.vehicle.year}
                    onChangeText={(v) => updateVehicle('year', v)}
                    placeholder="2020"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="numeric"
                  />
                </View>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('color')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.vehicle.color}
                    onChangeText={(v) => updateVehicle('color', v)}
                    placeholder="Black"
                    placeholderTextColor={COLORS.textMuted}
                  />
                </View>
              </View>

              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('vin')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.vehicle.vin}
                  onChangeText={(v) => updateVehicle('vin', v)}
                  placeholder="1HGBH41JXMN109186"
                  placeholderTextColor={COLORS.textMuted}
                  autoCapitalize="characters"
                />
              </View>

              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('mileage')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.vehicle.mileage}
                  onChangeText={(v) => updateVehicle('mileage', v)}
                  placeholder="50000"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="numeric"
                />
              </View>
            </View>
          )}

          {/* Step 2: Seller Info */}
          {step === 2 && (
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>{t('sellerInfo')}</Text>
              
              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('sellerName')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.seller.name}
                  onChangeText={(v) => updateSeller('name', v)}
                  placeholder="John Smith"
                  placeholderTextColor={COLORS.textMuted}
                />
              </View>

              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('phone')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.seller.phone}
                  onChangeText={(v) => updateSeller('phone', v)}
                  placeholder="+1 234 567 8900"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="phone-pad"
                />
              </View>

              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('address')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.seller.address}
                  onChangeText={(v) => updateSeller('address', v)}
                  placeholder="123 Main Street"
                  placeholderTextColor={COLORS.textMuted}
                />
              </View>

              <View style={styles.row}>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('city')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.seller.city}
                    onChangeText={(v) => updateSeller('city', v)}
                    placeholder="Chicago"
                    placeholderTextColor={COLORS.textMuted}
                  />
                </View>
                <View style={styles.inputHalf}>
                  <Text style={styles.label}>{t('state')}</Text>
                  <TextInput
                    style={styles.input}
                    value={formData.seller.state}
                    onChangeText={(v) => updateSeller('state', v)}
                    placeholder="IL"
                    placeholderTextColor={COLORS.textMuted}
                    maxLength={2}
                    autoCapitalize="characters"
                  />
                </View>
              </View>

              <View style={styles.inputFull}>
                <Text style={styles.label}>{t('zipCode')}</Text>
                <TextInput
                  style={styles.input}
                  value={formData.seller.zip_code}
                  onChangeText={(v) => updateSeller('zip_code', v)}
                  placeholder="60601"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="numeric"
                />
              </View>
            </View>
          )}

          {/* Step 3: Package Selection */}
          {step === 3 && (
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>{t('selectPackage')}</Text>
              
              {packages.map((pkg) => (
                <TouchableOpacity
                  key={pkg.id}
                  style={[
                    styles.packageCard,
                    formData.package_type === pkg.id && styles.packageCardActive,
                    pkg.isPro && styles.packageCardPro,
                  ]}
                  onPress={() => setFormData({ ...formData, package_type: pkg.id })}
                >
                  {pkg.isPro && <Text style={styles.recommendedBadge}>{t('recommended')}</Text>}
                  <View style={styles.packageHeader}>
                    <Text style={styles.packageName}>{pkg.name}</Text>
                    <Text style={styles.packagePrice}>${pkg.price}</Text>
                  </View>
                  <Text style={styles.packageDesc}>{pkg.desc}</Text>
                  <View style={styles.packageFeatures}>
                    {pkg.features.map((f, i) => (
                      <View key={i} style={styles.featureRow}>
                        <Ionicons name="checkmark-circle" size={16} color={COLORS.primary} />
                        <Text style={styles.featureText}>{f}</Text>
                      </View>
                    ))}
                  </View>
                </TouchableOpacity>
              ))}

              <Text style={styles.tipLabel}>{t('tip')}</Text>
              <View style={styles.tipOptions}>
                {APP_CONFIG.tipOptions.map((amount) => (
                  <TouchableOpacity
                    key={amount}
                    style={[
                      styles.tipOption,
                      formData.tip_amount === amount && styles.tipOptionActive,
                    ]}
                    onPress={() => setFormData({ ...formData, tip_amount: amount })}
                  >
                    <Text
                      style={[
                        styles.tipOptionText,
                        formData.tip_amount === amount && styles.tipOptionTextActive,
                      ]}
                    >
                      {amount === 0 ? t('noTip') : `$${amount}`}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>{t('confirm')}</Text>
              
              <View style={styles.summaryCard}>
                <Text style={styles.summaryLabel}>{t('vehicleInfo')}</Text>
                <Text style={styles.summaryValue}>
                  {formData.vehicle.year} {formData.vehicle.make} {formData.vehicle.model} - {formData.vehicle.color}
                </Text>
              </View>

              <View style={styles.summaryCard}>
                <Text style={styles.summaryLabel}>{t('sellerInfo')}</Text>
                <Text style={styles.summaryValue}>
                  {formData.seller.address}, {formData.seller.city}, {formData.seller.state} {formData.seller.zip_code}
                </Text>
              </View>

              <View style={styles.summaryCard}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>{t('packages')} ({selectedPackage?.name})</Text>
                  <Text style={styles.summaryValue}>${selectedPackage?.price}</Text>
                </View>
                {formData.tip_amount > 0 && (
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>{t('tip')}</Text>
                    <Text style={styles.summaryValue}>${formData.tip_amount}</Text>
                  </View>
                )}
                <View style={[styles.summaryRow, styles.summaryTotal]}>
                  <Text style={styles.summaryTotalLabel}>{t('total')}</Text>
                  <Text style={styles.summaryTotalValue}>${totalAmount}</Text>
                </View>
              </View>

              <TextInput
                style={styles.notesInput}
                value={formData.notes}
                onChangeText={(v) => setFormData({ ...formData, notes: v })}
                placeholder="Additional notes for the inspector..."
                placeholderTextColor={COLORS.textMuted}
                multiline
              />
            </View>
          )}
        </ScrollView>

        {/* Footer Buttons */}
        <View style={styles.footer}>
          {step > 1 && (
            <TouchableOpacity style={styles.backButton} onPress={() => setStep(step - 1)}>
              <Ionicons name="arrow-back" size={20} color={COLORS.text} />
              <Text style={styles.backButtonText}>{t('back')}</Text>
            </TouchableOpacity>
          )}
          
          {step < 4 ? (
            <TouchableOpacity
              style={[styles.nextButton, !canProceed() && styles.buttonDisabled]}
              onPress={() => setStep(step + 1)}
              disabled={!canProceed()}
            >
              <Text style={styles.nextButtonText}>{t('next')}</Text>
              <Ionicons name="arrow-forward" size={20} color={COLORS.background} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.submitButton, loading && styles.buttonDisabled]}
              onPress={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={COLORS.background} />
              ) : (
                <>
                  <Text style={styles.submitButtonText}>{t('submit')}</Text>
                  <Ionicons name="checkmark" size={20} color={COLORS.background} />
                </>
              )}
            </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.border,
  },
  progressDotActive: {
    backgroundColor: COLORS.primary,
    width: 24,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 120,
  },
  stepContent: {},
  stepTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 24,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  inputHalf: {
    flex: 1,
    marginBottom: 16,
  },
  inputFull: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 8,
  },
  input: {
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: COLORS.text,
  },
  packageCard: {
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
  },
  packageCardActive: {
    borderColor: COLORS.primary,
    backgroundColor: 'rgba(255, 191, 0, 0.05)',
  },
  packageCardPro: {
    borderColor: COLORS.primary,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.2,
    shadowRadius: 20,
  },
  recommendedBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.primary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 8,
  },
  packageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  packageName: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  packagePrice: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.primary,
  },
  packageDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 16,
  },
  packageFeatures: {
    gap: 8,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  featureText: {
    fontSize: 13,
    color: COLORS.textMuted,
  },
  tipLabel: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: 20,
    marginBottom: 12,
  },
  tipOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  tipOption: {
    flex: 1,
    paddingVertical: 14,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 10,
    alignItems: 'center',
  },
  tipOptionActive: {
    borderColor: COLORS.primary,
    backgroundColor: 'rgba(255, 191, 0, 0.1)',
  },
  tipOptionText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  tipOptionTextActive: {
    color: COLORS.primary,
  },
  summaryCard: {
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryTotal: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    marginBottom: 0,
  },
  summaryTotalLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text,
  },
  summaryTotalValue: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.primary,
  },
  notesInput: {
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: COLORS.text,
    minHeight: 100,
    textAlignVertical: 'top',
    marginTop: 12,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 20,
    paddingBottom: 36,
    backgroundColor: COLORS.background,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: 12,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 16,
    paddingHorizontal: 20,
  },
  backButtonText: {
    fontSize: 16,
    color: COLORS.text,
  },
  nextButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
  },
  nextButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.background,
  },
  submitButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.background,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
