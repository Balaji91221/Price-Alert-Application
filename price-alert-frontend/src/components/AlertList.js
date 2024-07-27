import React, { useState, useEffect } from 'react';
import { fetchAlerts, deleteAlert } from '../api';

const AlertList = () => {
    const [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState('');
    const [page, setPage] = useState(1);

    const loadAlerts = async () => {
        try {
            const data = await fetchAlerts(status, (page - 1) * 10, 10);
            setAlerts(data);
        } catch (error) {
            console.error(error);
            alert('Error fetching alerts');
        }
    };

    useEffect(() => {
        loadAlerts();
    }, [status, page]);

    const handleDelete = async (alertId) => {
        try {
            await deleteAlert(alertId);
            loadAlerts();
        } catch (error) {
            console.error(error);
            alert('Error deleting alert');
        }
    };

    return (
        <div>
            <div>
                <label>Status</label>
                <select value={status} onChange={(e) => setStatus(e.target.value)}>
                    <option value="">All</option>
                    <option value="created">Created</option>
                    <option value="triggered">Triggered</option>
                </select>
            </div>
            <ul>
                {alerts.map(alert => (
                    <li key={alert.id}>
                        {alert.coin_id} - {alert.target_price} - {alert.status}
                        <button onClick={() => handleDelete(alert.id)}>Delete</button>
                    </li>
                ))}
            </ul>
            <div>
                <button onClick={() => setPage(page - 1)} disabled={page === 1}>Previous</button>
                <button onClick={() => setPage(page + 1)}>Next</button>
            </div>
        </div>
    );
};

export default AlertList;
