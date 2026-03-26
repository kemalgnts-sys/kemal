import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Image,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';
import { t } from '../i18n';
import { COLORS, APP_CONFIG } from '../config';

const { width } = Dimensions.get('window');

// Login Screen
export const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert(t('error'), 'Please fill all fields');
      return;
    }

    setLoading(true);
    try {
      const user = await authApi.login(email, password);
      await login(user);
    } catch (e) {
      Alert.alert(t('error'), e.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.logoContainer}>
          <View style={styles.logoBox}>
            <Ionicons name="car-sport" size={40} color={COLORS.background} />
          </View>
          <Text style={styles.logoText}>{APP_CONFIG.name}</Text>
        </View>

        <Text style={styles.title}>{t('login')}</Text>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('email')}</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="email@example.com"
            placeholderTextColor={COLORS.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('password')}</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="••••••••"
            placeholderTextColor={COLORS.textMuted}
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          style={[styles.primaryButton, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.background} />
          ) : (
            <Text style={styles.primaryButtonText}>{t('login')}</Text>
          )}
        </TouchableOpacity>

        <View style={styles.linkContainer}>
          <Text style={styles.linkText}>{t('noAccount')} </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={styles.link}>{t('register')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// Register Screen
export const RegisterScreen = ({ navigation, route }) => {
  const initialType = route.params?.userType || 'buyer';
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    user_type: initialType,
  });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleRegister = async () => {
    if (!formData.email || !formData.password || !formData.full_name || !formData.phone) {
      Alert.alert(t('error'), 'Please fill all fields');
      return;
    }

    setLoading(true);
    try {
      const user = await authApi.register(formData);
      await login(user);
    } catch (e) {
      Alert.alert(t('error'), e.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.logoContainer}>
          <View style={styles.logoBox}>
            <Ionicons name="car-sport" size={40} color={COLORS.background} />
          </View>
          <Text style={styles.logoText}>{APP_CONFIG.name}</Text>
        </View>

        <Text style={styles.title}>{t('register')}</Text>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('accountType')}</Text>
          <View style={styles.typeSelector}>
            {['buyer', 'inspector'].map((type) => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.typeButton,
                  formData.user_type === type && styles.typeButtonActive,
                ]}
                onPress={() => setFormData({ ...formData, user_type: type })}
              >
                <Ionicons
                  name={type === 'buyer' ? 'person' : 'shield-checkmark'}
                  size={20}
                  color={formData.user_type === type ? COLORS.background : COLORS.textMuted}
                />
                <Text
                  style={[
                    styles.typeButtonText,
                    formData.user_type === type && styles.typeButtonTextActive,
                  ]}
                >
                  {t(type)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('fullName')}</Text>
          <TextInput
            style={styles.input}
            value={formData.full_name}
            onChangeText={(v) => setFormData({ ...formData, full_name: v })}
            placeholder="John Doe"
            placeholderTextColor={COLORS.textMuted}
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('email')}</Text>
          <TextInput
            style={styles.input}
            value={formData.email}
            onChangeText={(v) => setFormData({ ...formData, email: v })}
            placeholder="email@example.com"
            placeholderTextColor={COLORS.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('phone')}</Text>
          <TextInput
            style={styles.input}
            value={formData.phone}
            onChangeText={(v) => setFormData({ ...formData, phone: v })}
            placeholder="+1 234 567 8900"
            placeholderTextColor={COLORS.textMuted}
            keyboardType="phone-pad"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>{t('password')}</Text>
          <TextInput
            style={styles.input}
            value={formData.password}
            onChangeText={(v) => setFormData({ ...formData, password: v })}
            placeholder="••••••••"
            placeholderTextColor={COLORS.textMuted}
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          style={[styles.primaryButton, loading && styles.buttonDisabled]}
          onPress={handleRegister}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.background} />
          ) : (
            <Text style={styles.primaryButtonText}>{t('register')}</Text>
          )}
        </TouchableOpacity>

        <View style={styles.linkContainer}>
          <Text style={styles.linkText}>{t('hasAccount')} </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Login')}>
            <Text style={styles.link}>{t('login')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// Welcome/Landing Screen
export const WelcomeScreen = ({ navigation }) => {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.welcomeContent}>
        <View style={styles.heroSection}>
          <Image
            source={{ uri: 'https://images.unsplash.com/photo-1623659248894-1a0272243054?w=800' }}
            style={styles.heroImage}
          />
          <View style={styles.heroOverlay} />
          <View style={styles.heroContent}>
            <View style={styles.logoBox}>
              <Ionicons name="car-sport" size={32} color={COLORS.background} />
            </View>
            <Text style={styles.heroTitle}>{t('heroTitle')}</Text>
            <Text style={styles.heroSubtitle}>{t('heroSubtitle')}</Text>
          </View>
        </View>

        <View style={styles.ctaContainer}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => navigation.navigate('Register', { userType: 'buyer' })}
          >
            <Text style={styles.primaryButtonText}>{t('requestInspection')}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => navigation.navigate('Register', { userType: 'inspector' })}
          >
            <Text style={styles.secondaryButtonText}>{t('becomeInspector')}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={styles.linkButtonText}>{t('hasAccount')} <Text style={styles.link}>{t('login')}</Text></Text>
          </TouchableOpacity>
        </View>

        <View style={styles.howItWorks}>
          <Text style={styles.sectionTitle}>{t('howItWorks')}</Text>
          {[
            { icon: 'document-text', title: t('step1Title'), desc: t('step1Desc') },
            { icon: 'people', title: t('step2Title'), desc: t('step2Desc') },
            { icon: 'checkmark-circle', title: t('step3Title'), desc: t('step3Desc') },
          ].map((step, i) => (
            <View key={i} style={styles.stepCard}>
              <View style={styles.stepIcon}>
                <Ionicons name={step.icon} size={24} color={COLORS.primary} />
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>{step.title}</Text>
                <Text style={styles.stepDesc}>{step.desc}</Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 40,
  },
  welcomeContent: {
    paddingBottom: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoBox: {
    width: 64,
    height: 64,
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  logoText: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 24,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginBottom: 8,
  },
  input: {
    backgroundColor: COLORS.background,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: COLORS.text,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryButtonText: {
    color: COLORS.background,
    fontSize: 16,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: COLORS.text,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    marginTop: 12,
  },
  secondaryButtonText: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '700',
  },
  linkContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  linkText: {
    color: COLORS.textMuted,
    fontSize: 14,
  },
  link: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  linkButton: {
    alignItems: 'center',
    marginTop: 24,
  },
  linkButtonText: {
    color: COLORS.textMuted,
    fontSize: 14,
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: 12,
  },
  typeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  typeButtonText: {
    color: COLORS.textMuted,
    fontSize: 14,
    fontWeight: '600',
  },
  typeButtonTextActive: {
    color: COLORS.background,
  },
  heroSection: {
    height: 400,
    position: 'relative',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  heroContent: {
    position: 'absolute',
    bottom: 40,
    left: 24,
    right: 24,
  },
  heroTitle: {
    fontSize: 36,
    fontWeight: '800',
    color: COLORS.text,
    marginTop: 16,
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 16,
    color: COLORS.textMuted,
    lineHeight: 24,
  },
  ctaContainer: {
    padding: 24,
  },
  howItWorks: {
    padding: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 20,
  },
  stepCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  stepIcon: {
    width: 48,
    height: 48,
    backgroundColor: COLORS.elevated,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  stepDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    lineHeight: 20,
  },
});
