import { put, list, del } from '@vercel/blob';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Validate bearer token
  const authHeader = req.headers['authorization'] || '';
  const token = authHeader.replace(/^Bearer\s+/i, '');
  const expectedToken = process.env.DASHBOARD_PUSH_TOKEN;

  if (!expectedToken || token !== expectedToken) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);

    // Delete old blobs with same prefix to avoid accumulation
    const { blobs } = await list({ prefix: 'dashboard-data.json' });
    for (const blob of blobs) {
      await del(blob.url);
    }

    // Store new data
    const blob = await put('dashboard-data.json', body, {
      contentType: 'application/json',
      access: 'public',
      addRandomSuffix: false,
    });

    return res.status(200).json({ ok: true, url: blob.url });
  } catch (err) {
    console.error('Error storing blob:', err);
    return res.status(500).json({ error: 'internal', message: err.message });
  }
}
