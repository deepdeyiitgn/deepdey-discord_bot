// This file manages the connection to the MongoDB Atlas database.
// It uses a cached connection instance to improve performance in a serverless environment.
import { MongoClient } from 'mongodb';

const MONGODB_URI = process.env.MONGODB_URI;
const MONGODB_DB_NAME = process.env.MONGODB_DB_NAME;

if (!MONGODB_URI) {
    throw new Error('Please define the MONGODB_URI environment variable inside .env');
}
if (!MONGODB_DB_NAME) {
    throw new Error('Please define the MONGODB_DB_NAME environment variable inside .env');
}

// Using a global variable to cache the connection promise.
// This is a best practice for database connections in serverless functions.
let cachedClient: MongoClient | null = null;

export async function connectToDatabase() {
    if (cachedClient) {
        const db = cachedClient.db(MONGODB_DB_NAME);
        return { client: cachedClient, db };
    }

    const client = new MongoClient(MONGODB_URI!);

    await client.connect();
    
    cachedClient = client;
    const db = client.db(MONGODB_DB_NAME);

    return { client, db };
}