import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      // react-datepicker's "browser" field points at a UMD bundle that double-wraps
      // its default export; force resolution to the real ESM build instead so
      // `import DatePicker from 'react-datepicker'` yields the component, not the
      // module namespace object (fixes "Element type is invalid" at runtime).
      // Exact-match regex so it doesn't also swallow subpath imports like
      // 'react-datepicker/dist/react-datepicker.css'.
      {
        find: /^react-datepicker$/,
        replacement: fileURLToPath(
          new URL('./node_modules/react-datepicker/dist/es/index.js', import.meta.url),
        ),
      },
    ],
  },
  server: {
    host: true,
    allowedHosts: ['.ngrok-free.dev', '.ngrok-free.app', '.ngrok.io'],
  },
})
