import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { t } from './src/i18n';
import { COLORS } from './src/config';

// Screens
import { WelcomeScreen, LoginScreen, RegisterScreen } from './src/screens/AuthScreens';
import { BuyerDashboard, InspectionDetailScreen } from './src/screens/BuyerScreens';
import { InspectorDashboard, JobDetailScreen } from './src/screens/InspectorScreens';
import { NewInspectionScreen } from './src/screens/NewInspectionScreen';
import { NotificationsScreen, SettingsScreen } from './src/screens/CommonScreens';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Auth Stack (Welcome, Login, Register)
const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Welcome" component={WelcomeScreen} />
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

// Buyer Tab Navigator
const BuyerTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: false,
      tabBarStyle: {
        backgroundColor: COLORS.card,
        borderTopColor: COLORS.border,
        paddingBottom: 8,
        paddingTop: 8,
        height: 65,
      },
      tabBarActiveTintColor: COLORS.primary,
      tabBarInactiveTintColor: COLORS.textMuted,
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;
        if (route.name === 'Dashboard') iconName = focused ? 'home' : 'home-outline';
        else if (route.name === 'Notifications') iconName = focused ? 'notifications' : 'notifications-outline';
        else if (route.name === 'Settings') iconName = focused ? 'settings' : 'settings-outline';
        return <Ionicons name={iconName} size={24} color={color} />;
      },
    })}
  >
    <Tab.Screen name="Dashboard" component={BuyerDashboard} options={{ tabBarLabel: 'Home' }} />
    <Tab.Screen name="Notifications" component={NotificationsScreen} />
    <Tab.Screen name="Settings" component={SettingsScreen} />
  </Tab.Navigator>
);

// Inspector Tab Navigator
const InspectorTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: false,
      tabBarStyle: {
        backgroundColor: COLORS.card,
        borderTopColor: COLORS.border,
        paddingBottom: 8,
        paddingTop: 8,
        height: 65,
      },
      tabBarActiveTintColor: COLORS.primary,
      tabBarInactiveTintColor: COLORS.textMuted,
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;
        if (route.name === 'Dashboard') iconName = focused ? 'briefcase' : 'briefcase-outline';
        else if (route.name === 'Notifications') iconName = focused ? 'notifications' : 'notifications-outline';
        else if (route.name === 'Settings') iconName = focused ? 'settings' : 'settings-outline';
        return <Ionicons name={iconName} size={24} color={color} />;
      },
    })}
  >
    <Tab.Screen name="Dashboard" component={InspectorDashboard} options={{ tabBarLabel: 'Jobs' }} />
    <Tab.Screen name="Notifications" component={NotificationsScreen} />
    <Tab.Screen name="Settings" component={SettingsScreen} />
  </Tab.Navigator>
);

// Main App Navigator
const AppNavigator = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return null; // Or a loading screen
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!user ? (
        <Stack.Screen name="Auth" component={AuthStack} />
      ) : user.user_type === 'buyer' ? (
        <>
          <Stack.Screen name="BuyerMain" component={BuyerTabs} />
          <Stack.Screen name="NewInspection" component={NewInspectionScreen} options={{ presentation: 'modal' }} />
          <Stack.Screen name="InspectionDetail" component={InspectionDetailScreen} />
        </>
      ) : (
        <>
          <Stack.Screen name="InspectorMain" component={InspectorTabs} />
          <Stack.Screen name="JobDetail" component={JobDetailScreen} />
        </>
      )}
    </Stack.Navigator>
  );
};

// Main App Component
export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AuthProvider>
          <NavigationContainer
            theme={{
              dark: true,
              colors: {
                primary: COLORS.primary,
                background: COLORS.background,
                card: COLORS.card,
                text: COLORS.text,
                border: COLORS.border,
                notification: COLORS.primary,
              },
            }}
          >
            <StatusBar style="light" />
            <AppNavigator />
          </NavigationContainer>
        </AuthProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
