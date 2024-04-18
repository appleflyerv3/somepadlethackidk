// cors-proxy.js
export default async function handler(req, res) {
  const { method, headers, body } = req;
  const targetUrl = req.query.url;

  if (!targetUrl) {
    return res.status(400).json({ error: 'Missing target URL' });
  }

  try {
    const response = await fetch(targetUrl, {
      method,
      headers: {
        ...headers,
        'Access-Control-Allow-Origin': '*',
      },
      body,
    });

    const data = await response.text();
    const proxiedHeaders = {};

    response.headers.forEach((value, key) => {
      proxiedHeaders[key] = value;
    });

    res.status(response.status);
    res.writeHead(response.status, response.statusText, proxiedHeaders);
    res.end(data);
  } catch (error) {
    console.error('Error in CORS proxy:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
}
