import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import { 
  Compass, 
  Send, 
  MapPin, 
  Calendar, 
  IndianRupee, 
  CloudSun, 
  ChevronRight, 
  Loader2, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  Navigation,
  Utensils,
  Hotel,
  Shield,
  HelpCircle
} from 'lucide-react';

// Leaflet default marker fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const QUICK_TRIPS = [
  { city: "Ooty", days: 2, budget: 5000, desc: "Hill station getaway", img: "🌲" },
  { city: "Coorg", days: 3, budget: 12000, desc: "Coffee estates & waterfalls", img: "☕" },
  { city: "Munnar", days: 2, budget: 7000, desc: "Tea gardens & lakes", img: "🍃" },
];

export default function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentStep, setAgentStep] = useState(0);
  const [error, setError] = useState(null);
  const [plan, setPlan] = useState(null);
  const [activeTab, setActiveTab] = useState('itinerary');
  const [selectedPlace, setSelectedPlace] = useState(null);
  
  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([]);
  
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);

  // Multi-agent progress simulation steps
  const agentSteps = [
    { name: "Travel Coordinator", action: "Parsing travel request & parameters..." },
    { name: "Place Recommendation Agent", action: "Retrieving tourist spots and food options..." },
    { name: "Weather Agent", action: "Retrieving forecasts from Open-Meteo & compiling advice..." },
    { name: "Budget Agent", action: "Calculating travel costs & optimizing stay options..." },
    { name: "Itinerary Agent", action: "Scheduling day-by-day hourly activities..." }
  ];

  // Map initialization and updates
  useEffect(() => {
    if (plan && plan.recommended_places && mapRef.current) {
      // Clear previous map instance if it exists
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }

      const firstPlace = plan.recommended_places[0];
      const defaultLat = firstPlace?.latitude || 11.4102;
      const defaultLon = firstPlace?.longitude || 76.6950;

      // Create map
      mapInstance.current = L.map(mapRef.current).setView([defaultLat, defaultLon], 12);

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(mapInstance.current);

      // Clear existing markers
      markersRef.current = [];

      // Add markers for each place
      plan.recommended_places.forEach((place) => {
        if (place.latitude && place.longitude) {
          const marker = L.marker([place.latitude, place.longitude])
            .addTo(mapInstance.current)
            .bindPopup(`
              <div style="font-family: sans-serif; font-size: 13px;">
                <strong style="color: #9333ea;">${place.name}</strong><br/>
                ${place.category} | ⭐ ${place.rating}<br/>
                Entry: ₹${place.entry_fee}
              </div>
            `);
          markersRef.current.push({ name: place.name, marker });
        }
      });
    }

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [plan]);

  // Center map on selected place
  useEffect(() => {
    if (selectedPlace && mapInstance.current) {
      const match = markersRef.current.find(m => m.name === selectedPlace.name);
      if (match) {
        mapInstance.current.setView([selectedPlace.latitude, selectedPlace.longitude], 14);
        match.marker.openPopup();
      }
    }
  }, [selectedPlace]);

  // Handle plan submission
  const handleSubmitPlan = async (searchQuery) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    setPlan(null);
    setAgentStep(0);

    // Simulated step transitions for visual UX
    const interval = setInterval(() => {
      setAgentStep((prev) => {
        if (prev < agentSteps.length - 1) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, 1500);

    try {
      const backendUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: searchQuery })
      });

      if (!response.ok) {
        throw new Error('Backend failed to generate plan. Ensure uvicorn main:app is running.');
      }

      const data = await response.json();
      clearInterval(interval);
      setPlan(data);
      setMessages([
        { sender: 'user', text: searchQuery },
        { sender: 'coordinator', text: data.consolidated_report || `Here is your travel plan for ${data.destination}! I coordinated with the Place, Weather, Budget, and Itinerary agents to optimize this for you. Let me know if you want to make any changes.` }
      ]);
    } catch (err) {
      clearInterval(interval);
      setError(err.message || 'An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  // Handle follow up chat message
  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || loading) return;

    const userMsg = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');
    setLoading(true);

    try {
      const backendUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Regarding the trip to ${plan.destination}: ${userMsg}` })
      });

      if (!response.ok) throw new Error('Refining plan failed.');

      const data = await response.json();
      setPlan(data); // Update with the new refined plan
      setMessages(prev => [...prev, { 
        sender: 'coordinator', 
        text: data.consolidated_report || `I have updated your plan based on your request. Take a look at the revised budget, itinerary, or recommended locations!` 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        sender: 'coordinator', 
        text: `Sorry, I had trouble contacting my sub-agents to update the plan. Error: ${err.message}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setPlan(null)}>
            <div className="bg-purple-600 p-2 rounded-xl text-white shadow-lg shadow-purple-500/20">
              <Compass className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">Pakathu<span className="text-purple-500">Spot</span></h1>
              <p className="text-[10px] text-slate-400">Multi-Agent AI Travel Companion</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-xs text-slate-300">Agents Online</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col justify-center">
        {!plan && !loading && (
          /* Landing Screen */
          <div className="max-w-3xl mx-auto w-full text-center space-y-8 py-8 animate-fade-in">
            <div className="space-y-4">
              <div className="inline-flex items-center space-x-2 bg-purple-500/10 border border-purple-500/25 px-3 py-1 rounded-full text-purple-400 text-sm">
                <span>⚡ Freestyle Capstone Project</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-black tracking-tight text-white leading-tight">
                Your Next Adventure,<br/> Planned in Seconds by <span className="text-purple-400">Cooperating AI Agents</span>
              </h2>
              <p className="text-slate-400 text-base md:text-lg max-w-xl mx-auto">
                Enter your destination, days, and budget. Our coordinator agent delegating tasks to dedicated Place, Weather, and Budget agents will craft a custom trip for you.
              </p>
            </div>

            {/* Input Search Card */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-purple-500/5 w-64 h-64 rounded-full blur-3xl pointer-events-none"></div>
              
              <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-2">
                <div className="relative flex-1">
                  <MapPin className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder='Try: "Plan a 2-day trip to Ooty under ₹5000"'
                    className="w-full bg-slate-950 border border-slate-800 pl-10 pr-4 py-3 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition"
                  />
                </div>
                <button
                  onClick={() => handleSubmitPlan(query)}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-3 rounded-xl flex items-center justify-center space-x-2 transition shadow-lg shadow-purple-500/25 cursor-pointer"
                >
                  <span>Build Plan</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Quickstart suggestions */}
            <div className="space-y-3">
              <p className="text-xs text-slate-400 font-medium">POPULAR SUGGESTIONS</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {QUICK_TRIPS.map((trip) => (
                  <button
                    key={trip.city}
                    onClick={() => {
                      const q = `Plan a ${trip.days}-day trip to ${trip.city} under ₹${trip.budget}`;
                      setQuery(q);
                      handleSubmitPlan(q);
                    }}
                    className="bg-slate-900 border border-slate-800 hover:border-purple-500/50 p-4 rounded-xl text-left flex items-center space-x-3 transition cursor-pointer hover:bg-slate-900/80"
                  >
                    <span className="text-2xl">{trip.img}</span>
                    <div>
                      <h3 className="font-bold text-white text-sm">{trip.city}</h3>
                      <p className="text-xs text-slate-400">{trip.days} Days • Under ₹{trip.budget}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Loading Multi-Agent Screen */}
        {loading && !plan && (
          <div className="max-w-md mx-auto w-full bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl text-center space-y-6 animate-pulse">
            <div className="relative inline-flex">
              <div className="h-16 w-16 rounded-full border-4 border-purple-500/20 border-t-purple-600 animate-spin"></div>
              <Compass className="absolute top-5 left-5 h-6 w-6 text-purple-400 animate-bounce" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white">Coordinating Agent Workspace</h3>
              <p className="text-sm text-slate-400">Our agents are communicating to formulate your custom plan...</p>
            </div>

            {/* Agent steps display */}
            <div className="text-left space-y-3 border-t border-slate-800 pt-4">
              {agentSteps.map((step, idx) => {
                const isActive = idx === agentStep;
                const isPassed = idx < agentStep;
                return (
                  <div key={step.name} className={`flex items-start space-x-3 transition-colors ${isActive ? 'text-purple-400' : isPassed ? 'text-slate-400' : 'text-slate-600'}`}>
                    <div className="mt-1">
                      {isPassed ? (
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                      ) : isActive ? (
                        <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-slate-700 bg-slate-950 flex items-center justify-center text-[10px]">{idx + 1}</div>
                      )}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold">{step.name}</h4>
                      {isActive && <p className="text-[10px] text-slate-300 mt-0.5 animate-pulse">{step.action}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-md mx-auto w-full bg-slate-900 border border-red-500/30 p-6 rounded-2xl text-center space-y-4">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto" />
            <h3 className="text-lg font-bold text-white">Pipeline Execution Failed</h3>
            <p className="text-sm text-slate-400">{error}</p>
            <button
              onClick={() => setError(null)}
              className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-xl text-xs transition cursor-pointer"
            >
              Go Back
            </button>
          </div>
        )}

        {/* Travel Plan Dashboard (Loaded State) */}
        {plan && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch animate-fade-in">
            
            {/* Left Side: Chat & Map (4 Columns) */}
            <div className="lg:col-span-5 flex flex-col space-y-6">
              
              {/* AI Chat Console */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[320px] overflow-hidden shadow-xl">
                <div className="border-b border-slate-800 px-4 py-3 bg-slate-950/40 flex items-center space-x-2">
                  <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                  <span className="text-xs font-bold text-slate-300">Travel Coordinator Console</span>
                </div>
                
                {/* Message Log */}
                <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
                  {messages.map((m, idx) => (
                    <div key={idx} className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-xl px-3 py-2 ${
                        m.sender === 'user' 
                          ? 'bg-purple-600 text-white rounded-br-none' 
                          : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'
                      }`}>
                        <p className="font-semibold text-[10px] mb-0.5 opacity-70">
                          {m.sender === 'user' ? 'You' : 'Coordinator Agent'}
                        </p>
                        <p className="whitespace-pre-wrap">{m.text}</p>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-800 border border-slate-700 rounded-xl rounded-bl-none px-3 py-2 flex items-center space-x-2 text-slate-400">
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-400" />
                        <span>Updating plan...</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Chat Input */}
                <form onSubmit={handleSendChat} className="border-t border-slate-800 p-2 flex space-x-2 bg-slate-950/20">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask Coordinator to adjust (e.g. 'Add a tea estate visit')"
                    className="flex-1 bg-slate-950 border border-slate-800 px-3 py-2 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500"
                  />
                  <button 
                    type="submit"
                    className="bg-purple-600 hover:bg-purple-700 p-2 rounded-lg text-white transition cursor-pointer"
                  >
                    <Send className="h-3.5 w-3.5" />
                  </button>
                </form>
              </div>

              {/* Leaflet Map Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col h-[280px]">
                <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
                  <div className="flex items-center space-x-2 text-xs font-bold text-slate-300">
                    <Navigation className="h-4 w-4 text-purple-400" />
                    <span>Interactive Map</span>
                  </div>
                  <span className="text-[10px] text-slate-500">Click markers to view details</span>
                </div>
                <div className="flex-1 z-10" ref={mapRef} style={{ background: '#0f172a' }}></div>
              </div>

            </div>

            {/* Right Side: Tabbed plan details (7 Columns) */}
            <div className="lg:col-span-7 flex flex-col space-y-6">
              
              {/* Tab Navigation */}
              <div className="bg-slate-900 border border-slate-800 p-1.5 rounded-xl flex space-x-1">
                {[
                  { id: 'itinerary', label: 'Itinerary', icon: Calendar },
                  { id: 'places', label: 'Attractions', icon: MapPin },
                  { id: 'budget', label: 'Budget Summary', icon: IndianRupee },
                  { id: 'weather', label: 'Weather & Safety', icon: CloudSun }
                ].map((t) => {
                  const Icon = t.icon;
                  const isActive = activeTab === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setActiveTab(t.id)}
                      className={`flex-1 flex items-center justify-center space-x-1.5 py-2.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        isActive 
                          ? 'bg-purple-600 text-white shadow shadow-purple-500/20' 
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      <span className="hidden sm:inline">{t.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Tab content panel */}
              <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl overflow-y-auto max-h-[620px]">
                
                {/* 1. ITINERARY TAB */}
                {activeTab === 'itinerary' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                        <span>Day-by-Day Itinerary</span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-1">Generated and sequenced by the Itinerary Agent</p>
                    </div>

                    <div className="space-y-6 relative border-l border-purple-500/20 ml-2 pl-6">
                      {plan.itinerary.map((day) => (
                        <div key={day.day_number} className="relative space-y-3">
                          {/* Day marker dot */}
                          <div className="absolute -left-9 top-1 bg-purple-600 h-5 w-5 rounded-full border-4 border-slate-900 flex items-center justify-center text-[8px] font-bold text-white">
                            {day.day_number}
                          </div>
                          
                          <div>
                            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">Day {day.day_number}</span>
                            <h4 className="font-bold text-white text-sm">{day.theme}</h4>
                          </div>

                          <div className="grid gap-3">
                            {day.activities.map((act, aIdx) => {
                              const isLunch = act.place_name.includes("Restaurant") && act.time.includes("01:");
                              const isDinner = act.place_name.includes("Restaurant") && act.time.includes("08:");
                              return (
                                <div key={aIdx} className="bg-slate-950 border border-slate-800/50 p-4 rounded-xl flex items-start justify-between space-x-4 hover:border-slate-800 transition">
                                  <div className="flex items-start space-x-3">
                                    <div className="mt-1 bg-slate-900 p-1.5 rounded-lg border border-slate-800 text-slate-400">
                                      {isLunch || isDinner ? <Utensils className="h-3.5 w-3.5 text-amber-400" /> : <Clock className="h-3.5 w-3.5 text-blue-400" />}
                                    </div>
                                    <div className="space-y-1">
                                      <div className="flex items-center space-x-2">
                                        <span className="text-[10px] text-slate-400 font-bold bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">{act.time}</span>
                                        <span className="text-xs font-bold text-white">{act.place_name}</span>
                                      </div>
                                      <p className="text-[11px] text-slate-400 leading-relaxed">{act.activity_description}</p>
                                    </div>
                                  </div>
                                  {act.cost > 0 && (
                                    <span className="text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-full">
                                      ₹{act.cost}
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 2. ATTRACTIONS TAB */}
                {activeTab === 'places' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white">Recommended Attractions</h3>
                      <p className="text-xs text-slate-400 mt-1">Curated by the Place Agent using maps data</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {plan.recommended_places.map((place) => (
                        <div
                          key={place.name}
                          onClick={() => setSelectedPlace(place)}
                          className={`bg-slate-950 border p-4 rounded-xl flex flex-col justify-between space-y-3 cursor-pointer transition ${
                            selectedPlace?.name === place.name 
                              ? 'border-purple-500 ring-1 ring-purple-500/50 bg-slate-950/80 shadow-lg shadow-purple-500/5' 
                              : 'border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          <div className="space-y-2">
                            <div className="flex justify-between items-start space-x-2">
                              <h4 className="font-bold text-white text-xs leading-snug">{place.name}</h4>
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 shrink-0">
                                {place.category}
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">{place.description}</p>
                          </div>

                          <div className="border-t border-slate-900 pt-3 flex justify-between items-center text-[10px] text-slate-400">
                            <div className="flex items-center space-x-1.5">
                              <span className="text-amber-400">★</span>
                              <span className="font-bold text-slate-200">{place.rating.toFixed(1)}</span>
                            </div>
                            <div className="font-bold text-purple-400">
                              {place.entry_fee === 0 ? "Free Entry" : `Entry: ₹${place.entry_fee}`}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. BUDGET TAB */}
                {activeTab === 'budget' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white">Expense Breakdown</h3>
                      <p className="text-xs text-slate-400 mt-1">Calculated and optimized by the Budget Agent</p>
                    </div>

                    {/* Progress bar card */}
                    <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl space-y-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Total Estimated Cost</p>
                          <h4 className="text-2xl font-black text-white">₹{plan.budget_breakdown.total_estimated.toLocaleString('en-IN')}</h4>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-full border ${
                          plan.budget_breakdown.status.includes("Within") 
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          {plan.budget_breakdown.status}
                        </span>
                      </div>

                      {/* Visual progress bar comparing estimated vs limit */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] text-slate-400 font-bold">
                          <span>Limit: ₹{plan.budget_limit}</span>
                          <span>{Math.min(100, Math.round((plan.budget_breakdown.total_estimated / plan.budget_limit) * 100))}% Used</span>
                        </div>
                        <div className="h-2 bg-slate-900 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-1000 ${
                              plan.budget_breakdown.total_estimated <= plan.budget_limit 
                                ? 'bg-purple-600' 
                                : 'bg-amber-500'
                            }`}
                            style={{ width: `${Math.min(100, (plan.budget_breakdown.total_estimated / plan.budget_limit) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>

                    {/* Breakdown List */}
                    <div className="space-y-3">
                      {plan.budget_breakdown.categories.map((cat, idx) => {
                        // Category colors
                        const colors = [
                          'text-blue-400 bg-blue-500/10 border-blue-500/20',
                          'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
                          'text-amber-400 bg-amber-500/10 border-amber-500/20',
                          'text-purple-400 bg-purple-500/10 border-purple-500/20',
                          'text-rose-400 bg-rose-500/10 border-rose-500/20'
                        ];
                        const colClass = colors[idx % colors.length];
                        
                        return (
                          <div key={cat.category} className="bg-slate-950 border border-slate-800/60 p-4 rounded-xl flex items-center justify-between space-x-4">
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2">
                                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${colClass}`}>
                                  {cat.category}
                                </span>
                              </div>
                              <p className="text-[10px] text-slate-400 leading-normal">{cat.description}</p>
                            </div>
                            <span className="font-extrabold text-white text-sm shrink-0">
                              ₹{cat.amount.toLocaleString('en-IN')}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 4. WEATHER & SAFETY TAB */}
                {activeTab === 'weather' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white">Weather & Packing Safety Advice</h3>
                      <p className="text-xs text-slate-400 mt-1">Sourced from Open-Meteo & verified by the Weather Agent</p>
                    </div>

                    {/* Forecast row */}
                    <div className="grid grid-cols-2 gap-3">
                      {plan.weather_report.forecast.map((day) => (
                        <div key={day.day} className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-center space-y-2">
                          <span className="text-[9px] font-bold text-purple-400 block uppercase tracking-wider">{day.day}</span>
                          <span className="text-lg font-black text-white block">{day.temperature}</span>
                          <span className="text-[10px] font-semibold bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-300 inline-block">
                            {day.condition}
                          </span>
                          <p className="text-[9px] text-slate-500 mt-1 leading-normal">{day.advice}</p>
                        </div>
                      ))}
                    </div>

                    {/* Travel Advice Advisory tags */}
                    <div className="space-y-3 border-t border-slate-800 pt-4">
                      <h4 className="text-xs font-bold text-white flex items-center space-x-1.5">
                        <Shield className="h-4 w-4 text-purple-400" />
                        <span>Travel Advisory & Packing Tips</span>
                      </h4>
                      <ul className="grid gap-2">
                        {plan.travel_advice.map((adv, idx) => (
                          <li key={idx} className="bg-slate-950 border border-slate-800/40 p-3 rounded-lg flex items-start space-x-2 text-[10px] text-slate-300 leading-normal">
                            <span className="text-purple-500 font-bold mt-0.5 shrink-0">•</span>
                            <span>{adv}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                  </div>
                )}

              </div>
            </div>

          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center space-y-2">
          <p className="text-[10px] text-slate-500">
            PakathuSpot Travel Companion • freestyle capstone track. Built with FastAPI, Leaflet, and Google ADK.
          </p>
          <div className="flex justify-center space-x-4 text-[10px] text-slate-400">
            <span>No Hardcoded APIs</span>
            <span>•</span>
            <span>MCP Tool Compatible</span>
            <span>•</span>
            <span>Gemini LLM Refined</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
