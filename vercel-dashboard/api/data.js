import { list, head } from '@vercel/blob';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // List blobs to find our data file
    const { blobs } = await list({ prefix: 'dashboard-data.json' });

    if (!blobs || blobs.length === 0) {
      return res.status(200).json({ error: 'no_data', message: 'ממתין לנתונים...' });
    }

    // Fetch the blob content
    const blob = blobs[0];
    const response = await fetch(blob.url);
    const data = await response.json();

    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
    return res.status(200).json(data);
  } catch (err) {
    console.error('Error reading blob:', err);
    return res.status(500).json({ error: 'internal', message: err.message });
  }
}
