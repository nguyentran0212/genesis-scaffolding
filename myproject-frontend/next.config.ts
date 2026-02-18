import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard/workflows/',
        permanent: true, // Use 'true' for a 308 (SEO permanent), 'false' for 307 (Temporary)
      },
      {
        source: '/dashboard/',
        destination: '/dashboard/workflows/',
        permanent: true, // Use 'true' for a 308 (SEO permanent), 'false' for 307 (Temporary)
      },
    ];
  },
};

export default nextConfig;
