export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const ecfgId = process.env.EDGE_CONFIG_ID;
    const ecToken = process.env.EDGE_CONFIG_TOKEN;

    if (!ecfgId || !ecToken) {
      return res.status(500).json({ error: 'Missing EDGE_CONFIG_ID or EDGE_CONFIG_TOKEN env vars' });
    }

    // Read from Edge Config
    const ecRes = await fetch(
      `https://edge-config.vercel.com/${ecfgId}/item/dashboard_data?token=${ecToken}`
    );

    if (!ecRes.ok) {
      if (ecRes.status === 404) {
        return res.status(200).json({ error: 'no_data', message: 'ממתין לנתונים...' });
      }
      const errText = await ecRes.text();
      return res.status(500).json({ error: 'edge_config_read_failed', detail: errText });
    }

    const data = await ecRes.json();
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
    return res.status(200).json(data);
  } catch (err) {
    console.error('Error:', err);
    return res.status(500).json({ error: 'internal', message: err.message });
  }
}
