import eslint from '@eslint/js'
import globals from 'globals'
import vue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'

const typeScriptRules = {
  ...tseslint.configs.recommended[1].rules,
  ...tseslint.configs.recommended[2].rules,
  '@typescript-eslint/no-unused-vars': ['warn', {argsIgnorePattern: '^_', ignoreRestSiblings: true}],
}

export default [
  {
    ignores: [
      'coverage/**',
      'dist/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
    ],
  },
  eslint.configs.recommended,
  ...vue.configs['flat/essential'],
  {
    files: ['src/**/*.{js,ts,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: globals.browser,
      parserOptions: {
        parser: tseslint.parser,
      },
      sourceType: 'module',
    },
    rules: {
      // Keep existing cleanup debt visible without making initial adoption unusable.
      'no-unused-vars': ['warn', {argsIgnorePattern: '^_', ignoreRestSiblings: true}],
      'no-useless-escape': 'warn',
      'vue/multi-word-component-names': 'off',
      'vue/no-dupe-keys': 'warn',
      'vue/no-v-text-v-html-on-component': 'warn',
    },
  },
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: tseslint.parser,
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: typeScriptRules,
  },
  {
    files: ['src/**/*.vue'],
    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: typeScriptRules,
  },
  {
    files: ['test/**/*.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.vitest,
      },
      sourceType: 'module',
    },
  },
  {
    files: ['e2e/**/*.js', 'playwright.config.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: globals.node,
      sourceType: 'commonjs',
    },
  },
  {
    files: ['vite.config.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: globals.node,
      sourceType: 'module',
    },
  },
]
