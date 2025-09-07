/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'flagsapi.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
  // إعدادات لحل مشاكل hydration
  experimental: {
    optimizePackageImports: ['react-hot-toast'],
  },
  // إعدادات إضافية للاستقرار
  reactStrictMode: true,
  swcMinify: true,
};

export default nextConfig;