const express = require('express');
const {
    openDatabase,
    initSchemaAndSeed,
} = require('./db/database');
const { registerRoutes } = require('./routes');

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = openDatabase();
    await initSchemaAndSeed(db);
    registerRoutes(app, db);

    return { app, db };
}

module.exports = { createApp };
