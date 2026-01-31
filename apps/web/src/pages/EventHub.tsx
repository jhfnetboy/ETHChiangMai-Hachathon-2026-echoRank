import React, { useEffect, useState } from 'react';

// Mock data until API is connected
const MOCK_EVENTS = [
    { title: 'Chiang Mai Web3 Meetup', date: '2026-02-14 18:00', location: 'Yellow Coworking', url: '#' },
    { title: 'Nomad Coffee Club', date: '2026-02-15 10:00', location: 'Maya Mall', url: '#' },
];

export default function EventHub() {
    const [events, setEvents] = useState<any[]>(MOCK_EVENTS);
    const [loading, setLoading] = useState(false);

    // TODO: Connect to backend API
    // useEffect(() => {
    //     fetch('http://localhost:3000/api/events')
    //         .then(res => res.json())
    //         .then(data => setEvents(data));
    // }, []);

    return (
        <div className="min-h-screen bg-gray-900 text-white p-8">
            <header className="mb-10 text-center">
                <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    Chiang Mai Event Hub
                </h1>
                <p className="text-gray-400 mt-2">Aggregate. Discover. Connect.</p>
            </header>

            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {events.map((event, idx) => (
                    <div key={idx} className="bg-gray-800 rounded-xl p-6 hover:shadow-lg hover:shadow-purple-500/20 transition-all border border-gray-700 group">
                        <div className="flex justify-between items-start mb-4">
                            <span className="bg-purple-900/50 text-purple-300 text-xs font-mono py-1 px-2 rounded-md">
                                {event.source_domain || 'Unknown'}
                            </span>
                            <a href={event.url} target="_blank" className="text-gray-400 hover:text-white">
                                ↗
                            </a>
                        </div>
                        
                        <h3 className="text-xl font-bold mb-2 group-hover:text-purple-400 transition-colors">
                            {event.title}
                        </h3>
                        
                        <div className="space-y-2 text-sm text-gray-300">
                            <div className="flex items-center gap-2">
                                <span>📅</span>
                                <span>{event.date || 'TBD'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span>📍</span>
                                <span>{event.location || 'Chiang Mai'}</span>
                            </div>
                        </div>

                        <div className="mt-6 pt-4 border-t border-gray-700 flex justify-end">
                            <a 
                                href={event.url} 
                                target="_blank"
                                rel="noopener noreferrer"
                                className="bg-white text-black px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gray-200 transition-colors"
                            >
                                View Details
                            </a>
                        </div>
                    </div>
                ))}
            </div>

            {loading && (
                <div className="text-center mt-20 text-gray-500">
                    Loading AI curated events...
                </div>
            )}
        </div>
    );
}
