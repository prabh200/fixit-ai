import { useState } from 'react';
import { Wrench, Camera, Search, ShieldCheck, BrainCircuit, ClipboardCheck, MapPin, AlertTriangle, LoaderCircle, History, ExternalLink, CheckCircle2, PlayCircle, MessageSquarePlus } from 'lucide-react';

const API = 'http://localhost:8000';
const categories = ['appliance', 'plumbing', 'electrical', 'hvac', 'roofing', 'carpentry', 'pest control', 'general maintenance'];

export default function App() {
  const [area, setArea] = useState('Washing machine');
  const [category, setCategory] = useState('appliance');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [followUpAnswers, setFollowUpAnswers] = useState({});
  const [busy, setBusy] = useState(false);
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState('');
  const [requestStatus, setRequestStatus] = useState('');
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memory, setMemory] = useState(null);

  async function submitDiagnosis(fullDescription, isRefine = false) {
    if (isRefine) setRefining(true);
    else {
      setBusy(true);
      setResult(null);
      setSelectedProvider(null);
      setFollowUpAnswers({});
    }
    setError('');
    setRequestStatus('');

    try {
      const fd = new FormData();
      fd.append('appliance_or_area', area);
      fd.append('category', category);
      fd.append('description', fullDescription);
      fd.append('location', location);
      if (image) fd.append('image', image);
      const response = await fetch(`${API}/diagnose`, { method: 'POST', body: fd });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Diagnosis failed');
      setResult(data);
      setFollowUpAnswers({});
      if (data.nearby_providers?.length > 0) {
        setSelectedProvider(data.nearby_providers[0]);
      }
    } catch (err) {
      setError(err.message + '. Confirm the backend and Ollama are running.');
    } finally {
      setBusy(false);
      setRefining(false);
    }
  }

  function runDiagnosis(e) {
    e.preventDefault();
    submitDiagnosis(description, false);
  }

  function submitFollowUpAnswers(e) {
    e.preventDefault();
    const questions = result?.diagnosis?.follow_up_questions || [];
    const answeredLines = questions
      .map((q, idx) => {
        const ans = (followUpAnswers[idx] || '').trim();
        return ans ? `- Q: ${q}\n  A: ${ans}` : null;
      })
      .filter(Boolean);

    if (answeredLines.length === 0) return;

    const refinedDescription = `${description}\n\nAdditional details from user:\n${answeredLines.join('\n')}`;
    setDescription(refinedDescription);
    submitDiagnosis(refinedDescription, true);
  }

  async function prepareRequest() {
    if (!result) return;
    setRequestStatus('Saving request…');
    try {
      const response = await fetch(`${API}/repair-request`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          customer_name: 'Hackathon demo user',
          location: location || 'Not provided',
          category,
          problem_summary: result.diagnosis.problem_summary,
          diagnosis_id: result.diagnosis_id,
          selected_provider: selectedProvider ? `${selectedProvider.name} (${selectedProvider.address})` : 'No specific shop selected'
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not save request');
      const shopMsg = selectedProvider ? ` for ${selectedProvider.name}` : '';
      setRequestStatus(`Request ${data.request_id.slice(0,8)} saved${shopMsg}. No provider was contacted or appointment booked.`);
    } catch (err) { setRequestStatus(err.message); }
  }

  async function searchMemory(e) {
    e.preventDefault();
    try {
      const r = await fetch(`${API}/memory?q=${encodeURIComponent(memoryQuery)}`);
      setMemory(await r.json());
    } catch { setMemory({warning:'Memory service unavailable'}); }
  }

  const d = result?.diagnosis;
  const hasAnyFollowUpAnswer = Object.values(followUpAnswers).some(val => val && val.trim().length > 0);

  return <main className="shell">
    <header className="topbar">
      <div className="brand"><div className="brand-icon"><Wrench size={22}/></div><div><strong>FixIt<span>AI</span></strong><small>YOUR PERSONAL REPAIR AGENT</small></div></div>
      <div className="local-pill"><span/> Local AI · $0 API spend</div>
    </header>

    <section className="hero">
      <div className="eyebrow"><span className="pulse"/> HOUSEHOLD MAINTENANCE, REIMAGINED</div>
      <h1>When something breaks,<br/><em>we help you fix it.</em></h1>
      <p>Describe the problem. Share a photo. Your AI repair agent investigates, remembers your repair history, and builds a safe next-step plan.</p>
      <div className="feature-row">
        <span><BrainCircuit size={16}/> AI diagnosis</span><span><History size={16}/> Persistent memory</span><span><ShieldCheck size={16}/> Safety-first</span>
      </div>
    </section>

    <section className="layout">
      <form className="panel form-panel" onSubmit={runDiagnosis}>
        <div className="section-heading"><div><div className="eyebrow">STEP 01</div><h2>What needs fixing?</h2></div><Wrench/></div>
        <label>Repair category</label>
        <select value={category} onChange={e=>setCategory(e.target.value)}>
          {categories.map(c=><option key={c} value={c}>{c.replace(/\b\w/g,x=>x.toUpperCase())}</option>)}
        </select>
        <label>Appliance or area</label>
        <input value={area} onChange={e=>setArea(e.target.value)} placeholder="e.g. Samsung washer, kitchen sink, breaker panel" required/>
        <label>Describe what's happening</label>
        <textarea value={description} onChange={e=>setDescription(e.target.value)} placeholder="What happened? Any unusual sounds, smells, leaks, warning lights, or error codes?" required rows="5"/>
        <label>Your city or ZIP (optional)</label>
        <input value={location} onChange={e=>setLocation(e.target.value)} placeholder="e.g. San Francisco, CA"/>
        <label className="upload">
          <Camera size={20}/>
          <span>{image ? image.name : 'Add a photo (optional)'}</span>
          <small>JPG, PNG or WEBP · Max 8 MB</small>
          <input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>setImage(e.target.files?.[0] || null)}/>
        </label>
        <button className="primary" disabled={busy || refining || !description.trim()}>{busy ? <><LoaderCircle className="spin"/> Analyzing…</> : <>Diagnose my repair <Search size={17}/></>}</button>
        {error && <div className="error"><AlertTriangle size={17}/>{error}</div>}
      </form>

      <section className="results">
        {!d && <div className="empty panel"><div className="empty-icon"><BrainCircuit size={32}/></div><h2>Your repair plan starts here</h2><p>Submit a repair issue and FixIt AI will return possible causes, safe checks, and a next-step plan.</p><div className="mini-grid"><span>01 · Understand</span><span>02 · Diagnose</span><span>03 · Remember</span><span>04 · Plan action</span></div></div>}
        {d && <>
          <div className="panel diagnosis">
            <div className="section-heading"><div><div className="eyebrow">STEP 02 · AI ASSESSMENT</div><h2>Repair assessment</h2></div><span className={`status ${d.safety_level.toLowerCase()}`}>{d.safety_level}</span></div>
            <div className="summary">{d.problem_summary}</div>
            <div className="callout"><ShieldCheck size={19}/><div><b>Immediate next step</b><p>{d.immediate_action}</p></div></div>
            {d.safety_level === 'Emergency' && <div className="danger"><AlertTriangle/> Stop ordinary troubleshooting. Prioritize personal safety.</div>}
            <h3>Possible causes</h3>
            {(d.possible_causes || []).map((c,i)=><div className="cause" key={i}><div><b>{c.issue}</b><p>{c.explanation}</p></div><span>{c.likelihood}</span></div>)}
            <h3>Safe checks</h3>
            <ul>{(d.safe_checks || []).map((s,i)=><li key={i}>{s}</li>)}</ul>

            {d.follow_up_questions?.length > 0 && (
              <form onSubmit={submitFollowUpAnswers} style={{ marginTop: '16px', padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                  <MessageSquarePlus size={17} color="#34d399" />
                  <h3 style={{ margin: 0 }}>What we'd like to know (Answer to refine)</h3>
                </div>
                {d.follow_up_questions.map((q, i) => (
                  <div key={i} style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px', opacity: 0.9 }}>{q}</label>
                    <input
                      value={followUpAnswers[i] || ''}
                      onChange={e => setFollowUpAnswers(prev => ({ ...prev, [i]: e.target.value }))}
                      placeholder="Type your answer here..."
                      style={{ marginBottom: 0 }}
                    />
                  </div>
                ))}
                <button
                  type="submit"
                  className="secondary"
                  disabled={refining || !hasAnyFollowUpAnswer}
                  style={{ marginTop: '6px', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
                >
                  {refining ? <><LoaderCircle className="spin" size={16}/> Updating diagnosis…</> : 'Refine diagnosis with my answers'}
                </button>
              </form>
            )}

            <div className="cost"><div><small>ILLUSTRATIVE COST RANGE</small><strong>{d.cost_min_usd == null ? 'Not estimated' : `$${d.cost_min_usd} – $${d.cost_max_usd}`}</strong><p>{d.cost_note}</p></div><span>USD</span></div>
            <p className="disclaimer">AI-generated triage, not a professional inspection. Verify advice with the appliance manual or a qualified professional.</p>
          </div>

          {d.safety_level !== 'Emergency' && (result.diy_videos?.videos?.length > 0 || result.diy_videos?.search_url) && (
            <div className="panel action-panel">
              <div className="section-heading">
                <div>
                  <div className="eyebrow">DIY SELF-REPAIR GUIDES</div>
                  <h2>Watch similar repair tutorials</h2>
                </div>
                <PlayCircle />
              </div>

              {result.diy_videos?.videos?.length > 0 && (
                <div style={{ display: 'grid', gap: '10px', marginBottom: '12px' }}>
                  {result.diy_videos.videos.map((v, i) => (
                    <a
                      key={i}
                      href={v.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: 'flex',
                        gap: '12px',
                        alignItems: 'center',
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid rgba(255,255,255,0.1)',
                        background: 'rgba(255,255,255,0.03)',
                        textDecoration: 'none',
                        color: 'inherit'
                      }}
                    >
                      <img
                        src={v.thumbnail}
                        alt={v.title}
                        style={{ width: '112px', height: '64px', objectFit: 'cover', borderRadius: '6px', flexShrink: 0 }}
                      />
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontWeight: 600, fontSize: '13px', lineHeight: 1.3, marginBottom: '4px' }}>
                          {v.title}
                        </div>
                        <small style={{ opacity: 0.75, display: 'block' }}>
                          {v.channel}{v.duration ? ` · ${v.duration}` : ''}
                        </small>
                      </div>
                      <ExternalLink size={15} style={{ flexShrink: 0, opacity: 0.7 }} />
                    </a>
                  ))}
                </div>
              )}

              {result.diy_videos?.search_url && (
                <div className="links">
                  <a href={result.diy_videos.search_url} target="_blank" rel="noreferrer">
                    <span>Search more DIY tutorials on YouTube</span>
                    <small>Opens YouTube tutorials for {area} ({d.problem_summary})</small>
                  </a>
                </div>
              )}
            </div>
          )}

          <div className="panel action-panel">
            <div className="section-heading"><div><div className="eyebrow">STEP 03 · TAKE ACTION</div><h2>Find help & save plan</h2></div><MapPin/></div>

            {result.nearby_providers?.length > 0 && (
              <div style={{ marginBottom: '14px' }}>
                <small style={{ display: 'block', opacity: 0.75, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Nearby Repair Options (Click to select)
                </small>
                <div className="links">
                  {result.nearby_providers.map((shop, i) => {
                    const isSelected = selectedProvider?.name === shop.name && selectedProvider?.address === shop.address;
                    return (
                      <div
                        key={i}
                        onClick={() => setSelectedProvider(shop)}
                        style={{
                          padding: '12px 14px',
                          borderRadius: '10px',
                          border: isSelected ? '1px solid #34d399' : '1px solid rgba(255,255,255,0.12)',
                          background: isSelected ? 'rgba(52, 211, 153, 0.12)' : 'rgba(255,255,255,0.03)',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {isSelected && <CheckCircle2 size={15} color="#34d399" />}
                            {shop.name}
                          </span>
                          <a
                            href={shop.google_maps_url || shop.map_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{ fontSize: '12px', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}
                          >
                            Directions <ExternalLink size={12} />
                          </a>
                        </div>
                        <small style={{ display: 'block', marginTop: '4px', opacity: 0.75 }}>{shop.address}</small>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {result.provider_search?.length ? (
              <div className="links">
                {result.provider_search.map((p,i)=>(
                  <a key={i} href={p.url} target="_blank" rel="noreferrer">
                    <span>{p.name}</span>
                    <small>{p.note}</small>
                  </a>
                ))}
              </div>
            ) : (
              <p className="muted">Add your city or ZIP in Step 01 to find nearby repair shops.</p>
            )}

            <button className="primary" onClick={prepareRequest}>
              <ClipboardCheck size={17}/> {selectedProvider ? `Prepare request for ${selectedProvider.name}` : 'Prepare repair request'}
            </button>
            {requestStatus && <div className="success">{requestStatus}</div>}
            <div className="memory-note"><BrainCircuit size={18}/><div><b>Memory status: {result.memory_status?.provider || 'local'}</b><p>{result.memory_status?.warning ? 'Local memory saved; Cognee reported a setup issue.' : 'This repair record was saved for future recall.'}</p></div></div>
          </div>
        </>}
      </section>
    </section>

    <section className="panel memory-panel">
      <div className="section-heading"><div><div className="eyebrow">COGNEE · LONG-TERM MEMORY</div><h2>Ask about repair history</h2></div><History/></div>
      <form className="memory-search" onSubmit={searchMemory}>
        <input value={memoryQuery} onChange={e=>setMemoryQuery(e.target.value)} placeholder="e.g. washing machine or previous leak" required/>
        <button className="secondary">Recall</button>
      </form>
      {memory && <pre className="memory-output">{JSON.stringify(memory,null,2)}</pre>}
    </section>
    <footer>FixIt AI · Local-first prototype · No paid API calls · Always prioritize safety</footer>
  </main>;
}