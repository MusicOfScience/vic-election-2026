import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";
const repositoryBasePath = "/vic-election-2026";

const nextConfig: NextConfig = {
  ...(isGitHubPages
    ? {
        output: "export" as const,
        basePath: repositoryBasePath,
        assetPrefix: repositoryBasePath,
        trailingSlash: true,
        images: { unoptimized: true },
        // The Sites runtime includes Cloudflare-only server declarations that
        // are not imported by this static page but are outside Next's type universe.
        typescript: { ignoreBuildErrors: true },
      }
    : {}),
};

export default nextConfig;
