const { createApp } = require('./app');
const { settings } = require('./config/settings');

async function start() {
    const { app } = await createApp();

    app.listen(settings.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

start().catch((error) => {
    console.error('Falha ao iniciar a aplicação:', error.message);
    process.exit(1);
});
