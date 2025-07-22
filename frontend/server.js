const { createServer } = require("http");
const { parse } = require("url");
const next = require("next");
const { createProxyMiddleware } = require("http-proxy-middleware");
const WebSocket = require("ws");

const port = process.env.PORT || 13000;
const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer((req, res) => {
    handle(req, res);
  });

  const wsProxy = createProxyMiddleware({
    target: "ws://44.213.201.101:7860", // 确保 target 正确
    ws: true,
    pathFilter: '/socket/twilio-ws',
    pathRewrite: {
      '^/socket/twilio-ws': '/ws',
    },
  });

  server.on("upgrade", wsProxy.upgrade);
      
  server.listen(port, () => {
    console.log(`> Ready on http://localhost:${port}`);
  });
});
