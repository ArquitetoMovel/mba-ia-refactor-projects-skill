function decidePaymentStatus(cardNumber) {
    const card = String(cardNumber);
    return card.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = { decidePaymentStatus };
