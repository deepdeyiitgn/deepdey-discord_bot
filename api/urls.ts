// Vercel Serverless Function: /api/urls
// Handles GET and POST requests for the 'urls' collection in MongoDB.

import { connectToDatabase } from './lib/mongodb';
import type { ShortenedUrl } from '../types';

export default async function handler(req: any, res: any) {
    const { db } = await connectToDatabase();
    const urlsCollection = db.collection('urls');

    try {
        if (req.method === 'GET') {
            const urls = await urlsCollection.find({}).toArray();
            return res.status(200).json(urls);
        }

        if (req.method === 'POST') {
            const urls: ShortenedUrl[] = req.body;
            // This is a "replace all" operation, mirroring the previous KV store behavior.
            await urlsCollection.deleteMany({});
            if (urls.length > 0) {
                // The frontend sends Infinity as a special string, we need to handle it.
                const urlsToInsert = urls.map(url => ({
                    ...url,
                    expiresAt: url.expiresAt === Infinity ? '__Infinity__' : url.expiresAt
                }));
                await urlsCollection.insertMany(urlsToInsert);
            }
            return res.status(200).json({ success: true });
        }

        res.setHeader('Allow', ['GET', 'POST']);
        return res.status(405).end('Method Not Allowed');

    } catch (error: any) {
        console.error('Error with /api/urls:', error);
        return res.status(500).json({ error: error.message || 'An internal server error occurred.' });
    }
}