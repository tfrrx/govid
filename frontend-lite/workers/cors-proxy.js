/**
 * GoVid CORS 代理 - Cloudflare Worker
 *
 * 用途：绕过浏览器 CORS 限制，支持 B 站、YouTube 等需要特定 Headers 的平台
 * 部署：wrangler deploy workers/cors-proxy.js --name govid-cors-proxy
 *
 * 使用示例：
 * https://govid-cors-proxy.你的账号.workers.dev?url=https://xxx.bilivideo.com/video.m4s
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 处理 CORS 预检请求
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Max-Age': '86400',
        }
      });
    }

    // 获取目标 URL
    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response(
        JSON.stringify({ error: 'Missing url parameter' }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        }
      );
    }

    try {
      // 解析目标平台
      const target = new URL(targetUrl);
      const headers = new Headers();

      // 根据平台注入必需的 Headers
      if (target.hostname.includes('bilivideo') || target.hostname.includes('bilibili')) {
        // B 站 CDN 需要 Referer
        headers.set('Referer', 'https://www.bilibili.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        headers.set('Origin', 'https://www.bilibili.com');
      } else if (target.hostname.includes('youtube') || target.hostname.includes('googlevideo')) {
        // YouTube 需要特定 User-Agent
        headers.set('Referer', 'https://www.youtube.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
      } else if (target.hostname.includes('xhscdn') || target.hostname.includes('xiaohongshu')) {
        // 小红书
        headers.set('Referer', 'https://www.xiaohongshu.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      } else if (target.hostname.includes('weibo')) {
        // 微博
        headers.set('Referer', 'https://weibo.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      }

      // 保留 Range 请求头（支持断点续传）
      const range = request.headers.get('Range');
      if (range) {
        headers.set('Range', range);
      }

      // 转发请求到目标 CDN
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: headers,
        // 流式传输，不等待全部下载完
        cf: {
          cacheTtl: 3600,
          cacheEverything: true,
        }
      });

      // 复制响应
      const newHeaders = new Headers(response.headers);

      // 添加 CORS 头
      newHeaders.set('Access-Control-Allow-Origin', '*');
      newHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
      newHeaders.set('Access-Control-Allow-Headers', '*');
      newHeaders.set('Access-Control-Expose-Headers', '*');

      // 保留 Content-Disposition（文件名）
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        newHeaders.set('Content-Disposition', contentDisposition);
      }

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });

    } catch (error) {
      return new Response(
        JSON.stringify({
          error: 'Proxy error',
          message: error.message,
          stack: error.stack,
        }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        }
      );
    }
  }
};
