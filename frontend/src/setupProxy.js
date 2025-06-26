const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      timeout: 30000, // 30 secondes de timeout
      proxyTimeout: 30000,
      onError: function (err, req, res) {
        console.error('Proxy Error:', err);
        res.writeHead(500, {
          'Content-Type': 'text/plain'
        });
        res.end('Proxy error: ' + err.message);
      },
      onProxyRes: function (proxyRes, req, res) {
        console.log('Proxy Response:', req.method, req.url, '→', proxyRes.statusCode);
      },
      onProxyReq: function (proxyReq, req, res) {
        console.log('Proxy Request:', req.method, req.url);
      }
    })
  );
}; 