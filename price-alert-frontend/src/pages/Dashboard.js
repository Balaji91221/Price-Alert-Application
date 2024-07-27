import React from 'react';
import AlertForm from '../components/AlertForm';
import AlertList from '../components/AlertList';

const Dashboard = () => {
    return (
        <div>
            <h1>Price Alert Dashboard</h1>
            <AlertForm />
            <AlertList />
        </div>
    );
};

export default Dashboard;
