export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const authHeader = req.headers['authorization'] || '';
  const token = authHeader.replace(/^Bearer\s+/i, '');
  const expectedToken = process.env.DASHBOARD_PUSH_TOKEN;

  if (!expectedToken || token !== expectedToken) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const body = typeof req.body === 'object' ? req.body : JSON.parse(req.body);

    const ecfgId = process.env.EDGE_CONFIG_ID;
    const vercelToken = process.env.VERCEL_API_TOKEN;

    if (!ecfgId || !vercelToken) {
      return res.status(500).json({ error: 'Missing EDGE_CONFIG_ID or VERCEL_API_TOKEN env vars' });
    }

    const teamId = process.env.VERCEL_TEAM_ID || '';
    const qs = teamId ? `?teamId=${teamId}` : '';

    // Write to Edge Config
    const ecRes = await fetch(
      `https://api.vercel.com/v1/edge-config/${ecfgId}/items${qs}`,
      {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${vercelToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: [
            { operation: 'upsert', key: 'dashboard_data', value: body },
            { operation: 'upsert', key: 'last_push', value: new Date().toISOString() },
          ],
        }),
      }
    );

    if (!ecRes.ok) {
      const errText = await ecRes.text();
      return res.status(500).json({ error: 'edge_config_write_failed', detail: errText });
    }

    return res.status(200).json({ ok: true, ts: new Date().toISOString() });
  } catch (err) {
    console.error('Error:', err);
    return res.status(500).json({ error: 'internal', message: err.message });
  }
}
