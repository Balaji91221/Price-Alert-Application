// api.js
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/';  // Replace with your backend URL

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Login Function
export const login = async (username, password) => {
    try {
        const response = await api.post('/token', new URLSearchParams({
            username,
            password
        }), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        });
        localStorage.setItem('token', response.data.access_token);
        return response.data;
    } catch (error) {
        console.error('Login failed:', error.response ? error.response.data : error.message);
        throw error;
    }
};

// Register Function
export const register = async (username, password, email) => {
    try {
        const response = await api.post('/register', { username, password, email });
        return response.data;
    } catch (error) {
        console.error('Registration failed:', error.response ? error.response.data : error.message);
        throw error;
    }
};

// Create Alert Function
export const createAlert = async (coin_id, target_price) => {
    try {
        const token = localStorage.getItem('token');
        const response = await api.post('/alerts/create/', { coin_id, target_price }, {
            headers: { Authorization: `Bearer ${token}` },
        });
        return response.data;
    } catch (error) {
        console.error('Create alert failed:', error.response ? error.response.data : error.message);
        throw error;
    }
};

// Delete Alert Function
export const deleteAlert = async (alert_id) => {
    try {
        const token = localStorage.getItem('token');
        const response = await api.delete(`/alerts/delete/${alert_id}`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        return response.data;
    } catch (error) {
        console.error('Delete alert failed:', error.response ? error.response.data : error.message);
        throw error;
    }
};

// Fetch Alerts Function
export const fetchAlerts = async (status, skip = 0, limit = 10) => {
    try {
        const token = localStorage.getItem('token');
        const response = await api.get('/alerts/', {
            params: { status, skip, limit },
            headers: { Authorization: `Bearer ${token}` },
        });
        return response.data;
    } catch (error) {
        console.error('Fetch alerts failed:', error.response ? error.response.data : error.message);
        throw error;
    }
};
