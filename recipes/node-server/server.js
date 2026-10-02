const http = require("node:http");

const port = Number(process.env.PORT || 3000);

const server = http.createServer((req, res) => {
  if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    return res.end("ok");
  }
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Hello from a Node.js server on Beaver");
});

server.listen(port, "0.0.0.0", () => console.log(`listening on 0.0.0.0:${port}`));

process.on("SIGTERM", () => server.close(() => process.exit(0)));
