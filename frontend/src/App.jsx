import React, { useState } from 'react';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [audience, setAudience] = useState('');
  const [campaign, setCampaign] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  
  const [genLoading, setGenLoading] = useState(false);
  const [generatedImg, setGeneratedImg] = useState(null);

  const handleFile = (e) => {
    if(e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setPreview(URL.createObjectURL(f));
      setResults(null);
      setGeneratedImg(null);
    }
  };

  const onAnalyze = async (e) => {
    e.preventDefault();
    if(!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('audience', audience);
      formData.append('campaign_info', campaign);

      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setResults(data);
    } catch(err) {
      console.error(err);
      alert("Error connecting to backend - is FastAPI running?");
    }
    setLoading(false);
  };

  const onGenerate = async () => {
    if(!file) return;
    setGenLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('prompt', "Optimize the ad to look more professional and vibrant");

      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setGeneratedImg(data.generated_image);
    } catch(err) {
      console.error(err);
      alert("Generation failed");
    }
    setGenLoading(false);
  };

  const downloadImage = () => {
    if (!generatedImg) return;
    
    // Convert base64 data URL to blob
    const link = document.createElement('a');
    link.href = generatedImg;
    link.download = `ad-optimization-${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>AI Ad Visual Optimizer</h1>
        <p>Elevate your visual marketing with intelligent design analysis</p>
      </header>

      <div className="main-grid">
        <div className="glass-panel" style={{ height: 'fit-content' }}>
          <form onSubmit={onAnalyze}>
            <label className="upload-area">
              <input type="file" hidden accept="image/*" onChange={handleFile} />
              {!preview ? (
                <div>
                  <h3 style={{color: 'white', marginBottom: '10px'}}>Drag & Drop Ad Image</h3>
                  <p style={{color: '#94a3b8'}}>or click to browse</p>
                </div>
              ) : (
                <img src={preview} alt="Preview" className="preview-img" style={{marginTop: 0}} />
              )}
            </label>

            <div className="form-group">
              <label>Target Audience</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g., Millennials, Tech Enthusiasts"
                value={audience}
                onChange={e => setAudience(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Campaign Objective</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g., Brand Awareness, Conversion"
                value={campaign}
                onChange={e => setCampaign(e.target.value)}
              />
            </div>

            <button type="submit" className="btn" disabled={!file || loading}>
              {loading ? "Analyzing Visuals..." : "Analyze Ad Design"}
            </button>
          </form>
        </div>

        {results ? (
          <div className="glass-panel" style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <h2 style={{marginBottom: '1.5rem', color: 'white'}}>Analysis Results</h2>
            <div className="results-grid">
              <div className="score-card">
                <div className="score-value">{results.scores.aesthetic}%</div>
                <div className="score-label">Aesthetic</div>
              </div>
              <div className="score-card">
                <div className="score-value" style={{color: '#f472b6'}}>{results.scores.readability}%</div>
                <div className="score-label">Readability</div>
              </div>
              <div className="score-card">
                <div className="score-value" style={{color: '#60a5fa'}}>{results.scores.contrast}%</div>
                <div className="score-label">Contrast</div>
              </div>
              <div className="score-card">
                <div className="score-value" style={{color: '#fbbf24'}}>{results.scores.layout}%</div>
                <div className="score-label">Layout</div>
              </div>
            </div>

            <div className="suggestions">
              <h3>AI Suggestions</h3>
              <ul>
                {results.suggestions.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>

            <div className="ocr-text">
              <h3>Extracted Text</h3>
              <p style={{color: '#cbd5e1', fontStyle: 'italic'}}>"{results.extracted_text}"</p>
            </div>

            <button onClick={onGenerate} className="btn generate-btn" disabled={genLoading}>
              {genLoading ? "Generating Variants..." : "Auto-Optimize Design (Generate Variant)"}
            </button>

            {generatedImg && (
              <div style={{marginTop: '2rem', animation: 'fadeIn 0.5s ease-out'}}>
                <h3 style={{color: 'white', marginBottom: '1rem'}}>Optimized Ad Vision</h3>
                <img src={generatedImg} alt="Generated" className="generated-img" />
                <button 
                  onClick={downloadImage} 
                  className="btn" 
                  style={{marginTop: '1rem', backgroundColor: '#10b981'}}
                >
                  ⬇ Download Optimized Image
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="glass-panel empty-state" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
            <p style={{ color: 'var(--text-sec)', textAlign: 'center', fontStyle: 'italic' }}>
              Upload an image and analyze it to see your results and optimization options here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
