import React, { useState } from 'react';
import { createAlert } from '../api';

const AlertForm = () => {
    const [coinId, setCoinId] = useState('');
    const [targetPrice, setTargetPrice] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createAlert(coinId, targetPrice);
            alert('Alert created successfully');
        } catch (error) {
            console.error(error);
            alert('Error creating alert');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label>Coin ID</label>
                <input type="text" value={coinId} onChange={(e) => setCoinId(e.target.value)} required />
            </div>
            <div>
                <label>Target Price</label>
                <input type="number" value={targetPrice} onChange={(e) => setTargetPrice(e.target.value)} required />
            </div>
            <button type="submit">Create Alert</button>
        </form>
    );
};

export default AlertForm;
