// expo-localization 55 no longer exports `locale`. Callers must use getLocales().

export function resolveDeviceLanguage(localization) {
  const fromLocales = languageFromGetLocales(localization);
  if (fromLocales) {
    return fromLocales;
  }

  const fromLegacy = languageFromLegacyLocale(localization);
  if (fromLegacy) {
    return fromLegacy;
  }

  return 'en';
}

function languageFromGetLocales(localization) {
  if (!localization || typeof localization.getLocales !== 'function') {
    return null;
  }

  let locales;
  try {
    locales = localization.getLocales();
  } catch {
    return null;
  }

  if (!Array.isArray(locales) || locales.length === 0) {
    return null;
  }

  const primary = locales[0] || {};
  return normalizeLanguageCode(primary.languageCode || primary.languageTag);
}

function languageFromLegacyLocale(localization) {
  if (!localization || typeof localization.locale !== 'string') {
    return null;
  }
  return normalizeLanguageCode(localization.locale);
}

function normalizeLanguageCode(value) {
  if (typeof value !== 'string') {
    return null;
  }
  const code = value.trim().toLowerCase().split('-')[0];
  return code || null;
}
