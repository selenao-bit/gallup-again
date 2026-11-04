/** Authoritative frontend identity and design tokens. Used by Vite HTML and React. */
export const theme = {
  brand: {
    name: 'Gallup Again',
    descriptor: 'Performance Review Assistant',
    description: 'Gallup Again helps managers prepare evidence-grounded performance conversations using permitted employee records.',
    mark: '↗',
  },
  color: {
    primary: '#002D62',
    primaryHover: '#001F45',
    secondaryBlue: '#174A7E',
    lightBlue: '#E8F0F8',
    blueHover: '#F0F5FA',
    buff: '#E4CF9F',
    paleBuff: '#F5ECD7',
    buffInk: '#735B2B',
    background: '#F7F9FC',
    surface: '#FFFFFF',
    surfaceSubtle: '#FBFCFE',
    text: '#17263B',
    textMuted: '#526277',
    textSubtle: '#607086',
    border: '#D8E1EC',
    borderSubtle: '#E4EAF2',
    borderStrong: '#8193AA',
    success: '#216346',
    successSurface: '#E9F4ED',
    successBorder: '#B8D8C5',
    error: '#9B3833',
    errorSurface: '#FFF2F0',
    errorBorder: '#E2B8B3',
    warning: '#805B13',
    warningSurface: '#FFF6DF',
    warningBorder: '#E7CF94',
  },
  font: {
    family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    mono: 'ui-monospace, SFMono-Regular, Consolas, monospace',
    bodySize: '14px',
    regular: '400',
    medium: '500',
    semibold: '600',
    heading: '650',
    bold: '700',
    brand: '750',
    lineHeight: '1.6',
  },
  radius: { small: '4px', control: '6px', button: '7px', card: '8px', panel: '9px', large: '12px', pill: '20px', round: '50%' },
  shadow: {
    workspace: '0 5px 18px rgb(0 45 98 / 3%)',
    popover: '0 10px 40px rgb(0 45 98 / 14%)',
  },
  space: { 1: '4px', 2: '8px', 3: '12px', 4: '16px', 5: '20px', 6: '24px', 7: '28px', 8: '32px' },
} as const

/** CSS custom properties are generated from the groups above, not maintained separately. */
export const themeCss = ':root {\n' + Object.entries(theme)
  .filter(([group]) => group !== 'brand')
  .flatMap(([group, values]) => Object.entries(values).map(([key, value]) =>
    `  --${group}-${key.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)}: ${value};`,
  ))
  .join('\n') + '\n}'
