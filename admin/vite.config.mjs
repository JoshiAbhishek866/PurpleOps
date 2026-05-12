import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'
import autoprefixer from 'autoprefixer'

export default defineConfig(() => {
  return {
    plugins: [vue()],
    base: './',
    css: {
      postcss: {
        plugins: [autoprefixer({})],
      },
    },
    resolve: {
      alias: [
        { find: /^~(.+)/, replacement: path.join(process.cwd(), 'node_modules/$1') },
        { find: /^@\//, replacement: path.join(process.cwd(), 'src') + '/' },
      ],
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue', '.scss'],
    },
    server: {
      port: 3001,
      host: '0.0.0.0',
      allowedHosts: 'all',
      proxy: {},
    },
  }
})
