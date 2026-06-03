import React, { useState, useEffect } from 'react';
import axios from 'axios';
import keycloak from './keycloak';

export default function App({ initialAuth }) {
    const [authenticated, setAuthenticated] = useState(initialAuth);
    const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'vault'

    // Upload State
    const [file, setFile] = useState(null);
    const [classification, setClassification] = useState('public');
    const [uploadResult, setUploadResult] = useState(null);

    // Vault Explorer State
    const [vaultFiles, setVaultFiles] = useState([]);
    const [selectedMeta, setSelectedMeta] = useState(null);

    // Global State
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const roles = keycloak.tokenParsed?.realm_access?.roles
        .filter(r => !['offline_access', 'uma_authorization', 'default-roles-secure-vault-realm'].includes(r))
        .join(', ') || 'None';

    const user = authenticated ? {
        username: keycloak.tokenParsed?.preferred_username,
        clearance: roles
    } : null;

    // Helper: Create an Axios instance with the current token
    const getApi = async () => {
        await keycloak.updateToken(30);
        return axios.create({
            baseURL: import.meta.env.VITE_API_BASE_URL,
            headers: { 'Authorization': `Bearer ${keycloak.token}` }
        });
    };

    // --- Vault Explorer Logic ---
    const fetchVaultFiles = async () => {
        setLoading(true);
        setError('');
        try {
            const api = await getApi();
            const res = await api.get('/list');
            setVaultFiles(res.data.files);
        } catch (err) {
            setError("Failed to load vault files.");
        } finally {
            setLoading(false);
        }
    };

    // Fetch files whenever the user switches to the 'vault' tab
    useEffect(() => {
        if (activeTab === 'vault') {
            fetchVaultFiles();
            setSelectedMeta(null); // Reset metadata view
        }
    }, [activeTab]);

    const handleViewMetadata = async (key) => {
        try {
            const api = await getApi();
            const res = await api.get(`/metadata?object_key=${encodeURIComponent(key)}`);
            setSelectedMeta({ key, data: res.data.metadata });
        } catch (err) {
            setError("Failed to fetch metadata.");
        }
    };

    const handleDownload = async (key) => {
        try {
            const api = await getApi();
            const res = await api.get(`/download-link?object_key=${encodeURIComponent(key)}`);
            // Open the securely signed AWS S3 URL in a new tab
            window.open(res.data.download_url, '_blank');
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to generate download link.");
        }
    };

    // --- Upload Logic ---
    const handleUpload = async (e) => {
        e.preventDefault();
        setError('');
        setUploadResult(null);
        setLoading(true);

        if (!file) {
            setError("Please select a file first.");
            setLoading(false);
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("classification", classification);

        try {
            const api = await getApi();
            const uploadRes = await api.post('/upload', formData);
            setUploadResult({ key: uploadRes.data.object_key });
            setFile(null); // Clear form
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Upload failed");
        } finally {
            setLoading(false);
        }
    };

    if (!authenticated) {
        return (
            <div style={{ maxWidth: '600px', margin: '50px auto', padding: '30px', background: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                <h2>🔐 Identity Verification</h2>
                <p>Authenticate with the central Identity Provider to access the vault.</p>
                <button onClick={() => keycloak.login()} style={{ background: '#3498db', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>
                    Login via Keycloak
                </button>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: '800px', margin: '50px auto', padding: '30px', background: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h2>📁 Secure Document Vault</h2>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div style={{ background: '#2ecc71', color: 'white', padding: '5px 15px', borderRadius: '20px', fontSize: '14px' }}>
                    User: {user?.username} | Clearance: [{user?.clearance}]
                </div>
                <button onClick={() => keycloak.logout()} style={{ background: '#e74c3c', color: 'white', padding: '6px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
                    Logout
                </button>
            </div>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '2px solid #eee', paddingBottom: '10px' }}>
                <button
                    onClick={() => setActiveTab('upload')}
                    style={{ background: activeTab === 'upload' ? '#3498db' : '#ecf0f1', color: activeTab === 'upload' ? 'white' : '#333', padding: '8px 16px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>
                    Upload Document
                </button>
                <button
                    onClick={() => setActiveTab('vault')}
                    style={{ background: activeTab === 'vault' ? '#3498db' : '#ecf0f1', color: activeTab === 'vault' ? 'white' : '#333', padding: '8px 16px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>
                    My Vault Explorer
                </button>
            </div>

            {error && <div style={{ background: '#fde8e8', color: '#9b1c1c', padding: '15px', borderRadius: '5px', marginBottom: '15px', fontWeight: 'bold' }}>❌ {error}</div>}

            {/* TAB 1: UPLOAD */}
            {activeTab === 'upload' && (
                <form onSubmit={handleUpload}>
                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Select File:</label>
                        <input type="file" onChange={(e) => setFile(e.target.files[0])} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}/>
                    </div>
                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Target Data Classification:</label>
                        <select value={classification} onChange={(e) => setClassification(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
                            <option value="public">Public (General Info)</option>
                            <option value="internal">Internal (Company Only)</option>
                            <option value="restricted">Restricted (Highly Sensitive)</option>
                        </select>
                    </div>
                    <button type="submit" disabled={loading} style={{ background: loading ? '#95a5a6' : '#3498db', color: 'white', padding: '12px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }}>
                        {loading ? 'Processing...' : 'Encrypt & Upload to S3'}
                    </button>

                    {uploadResult && (
                        <div style={{ background: '#e8f8f5', color: '#1abc9c', padding: '15px', borderRadius: '5px', marginTop: '15px', fontWeight: 'bold' }}>
                            ✅ File successfully persisted to: {uploadResult.key}
                        </div>
                    )}
                </form>
            )}

            {/* TAB 2: VAULT EXPLORER */}
            {activeTab === 'vault' && (
                <div>
                    {loading && <p>Loading secure vault contents...</p>}
                    {!loading && vaultFiles.length === 0 && <p>No accessible files found in your clearance scope.</p>}

                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {vaultFiles.map(key => (
                            <li key={key} style={{ background: '#f8f9fa', padding: '15px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#2c3e50', wordBreak: 'break-all' }}>{key}</span>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button onClick={() => handleViewMetadata(key)} style={{ background: '#f39c12', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Metadata</button>
                                    <button onClick={() => handleDownload(key)} style={{ background: '#2ecc71', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Download</button>
                                </div>
                            </li>
                        ))}
                    </ul>

                    {selectedMeta && (
                        <div style={{ borderTop: '2px solid #eee', marginTop: '20px', paddingTop: '20px' }}>
                            <h3>📄 Object Metadata</h3>
                            <p style={{ fontSize: '12px', color: '#7f8c8d' }}>{selectedMeta.key}</p>
                            <pre style={{ background: '#2c3e50', color: '#ecf0f1', padding: '15px', borderRadius: '5px', overflowX: 'auto' }}>
                                {JSON.stringify(selectedMeta.data, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
