// React Navigation 7 reads theme.fonts while configuring the native stack,
// including when the header is hidden. A colors-only theme throws on the
// first screen because fonts.regular is undefined.

export function buildNavigationTheme(baseTheme, colors) {
  return {
    ...baseTheme,
    dark: true,
    colors: {
      ...baseTheme.colors,
      ...colors,
    },
  };
}
