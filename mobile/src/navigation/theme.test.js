import assert from 'node:assert/strict';
import test from 'node:test';
import { buildNavigationTheme } from './theme.js';

// Same property access as @react-navigation/native-stack 7.14.9
// useHeaderConfigProps, which runs for every native stack screen.
function readNativeStackHeaderFont(theme) {
  const { fonts } = theme;
  return fonts.regular;
}

const baseTheme = {
  dark: false,
  colors: {
    primary: 'rgb(10, 132, 255)',
    background: 'rgb(1, 1, 1)',
    card: 'rgb(18, 18, 18)',
    text: 'rgb(229, 229, 231)',
    border: 'rgb(39, 39, 41)',
    notification: 'rgb(255, 69, 58)',
  },
  fonts: {
    regular: { fontFamily: 'System', fontWeight: '400' },
    medium: { fontFamily: 'System', fontWeight: '500' },
    bold: { fontFamily: 'System', fontWeight: '600' },
    heavy: { fontFamily: 'System', fontWeight: '700' },
  },
};

test('colors-only theme crashes native stack header setup', () => {
  const colorsOnly = {
    dark: true,
    colors: {
      primary: '#FFBF00',
      background: '#0A0A0A',
      card: '#141414',
      text: '#FFFFFF',
      border: '#262626',
      notification: '#FFBF00',
    },
  };

  assert.equal(colorsOnly.fonts, undefined);
  assert.throws(() => readNativeStackHeaderFont(colorsOnly), { name: 'TypeError' });
});

test('navigation theme keeps fonts and applies color overrides', () => {
  const theme = buildNavigationTheme(baseTheme, {
    primary: '#FFBF00',
    background: '#0A0A0A',
    card: '#141414',
    text: '#FFFFFF',
    border: '#262626',
    notification: '#FFBF00',
  });

  assert.equal(theme.dark, true);
  assert.equal(theme.fonts, baseTheme.fonts);
  assert.equal(readNativeStackHeaderFont(theme).fontWeight, '400');
  assert.equal(theme.fonts.medium.fontWeight, '500');
  assert.equal(theme.fonts.bold.fontWeight, '600');
  assert.equal(theme.fonts.heavy.fontWeight, '700');
  assert.equal(theme.colors.primary, '#FFBF00');
  assert.equal(theme.colors.background, '#0A0A0A');
  assert.equal(theme.colors.card, '#141414');
  assert.equal(theme.colors.text, '#FFFFFF');
  assert.equal(theme.colors.border, '#262626');
  assert.equal(theme.colors.notification, '#FFBF00');
});
