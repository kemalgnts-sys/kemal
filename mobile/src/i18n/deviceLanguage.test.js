import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveDeviceLanguage } from './deviceLanguage.js';

// Public exports of expo-localization@55.0.9 (locked in package-lock.json).
// `locale` was removed; the module namespace only exposes these functions.
function sdk55Localization(locales) {
  return {
    getLocales: () => locales,
    getCalendars: () => [],
    useLocales: () => locales,
    useCalendars: () => [],
  };
}

test('SDK 55 module namespace has no locale and used to crash on import', () => {
  const localization = sdk55Localization([
    { languageCode: 'tr', languageTag: 'tr-TR' },
  ]);

  assert.equal(localization.locale, undefined);
  assert.throws(
    () => localization.locale.split('-')[0],
    { name: 'TypeError' }
  );
  assert.equal(resolveDeviceLanguage(localization), 'tr');
});

test('uses languageTag when languageCode is missing', () => {
  const localization = sdk55Localization([
    { languageCode: null, languageTag: 'es-MX' },
  ]);
  assert.equal(resolveDeviceLanguage(localization), 'es');
});

test('falls back to the legacy locale string', () => {
  assert.equal(
    resolveDeviceLanguage({ locale: 'en-US' }),
    'en'
  );
});

test('falls back to English when locale data is missing or throws', () => {
  assert.equal(resolveDeviceLanguage(undefined), 'en');
  assert.equal(resolveDeviceLanguage({}), 'en');
  assert.equal(
    resolveDeviceLanguage({
      getLocales: () => {
        throw new Error('native module unavailable');
      },
    }),
    'en'
  );
  assert.equal(
    resolveDeviceLanguage(sdk55Localization([])),
    'en'
  );
});
