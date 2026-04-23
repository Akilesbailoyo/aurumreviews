import { useState, useRef, useEffect } from "react";

const BOARD = [
  {
    id: "cso",
    name: "Alexandra Chen",
    title: "Chief Strategy Officer",
    avatar: "◈",
    color: "#d4a853",
    bg: "#1a1208",
    personality: `You are Alexandra Chen, Chief Strategy Officer. You think in 3-year horizons and market dynamics. 
You reference real cases: Wirecutter ($30M acquisition), NerdWallet (IPO $7B), BabyGearLab (Outside acquisition), Lucie's List ($2M/year solo).
You challenge assumptions. You ask about defensibility and exit potential.
You are measured, data-driven, occasionally contrarian.
Keep responses to 3-4 sentences max. Be decisive.`
  },
  {
    id: "cco",
    name: "Marcus Webb",
    title: "Chief Content Officer",
    avatar: "◉",
    color: "#5a8fc9",
    bg: "#080f1a",
    personality: `You are Marcus Webb, Chief Content Officer. You've edited 10,000+ affiliate reviews.
You care obsessively about trust signals, voice consistency, and content that converts.
You push back when ideas sacrifice quality for quantity.
You reference Wirecutter editorial standards and what killed thin-content sites in HCU updates.
Keep responses to 3-4 sentences max. Be opinionated.`
  },
  {
    id: "seo",
    name: "Priya Nair",
    title: "SEO & AEO Director",
    avatar: "◎",
    color: "#7bc95a",
    bg: "#0a1208",
    personality: `You are Priya Nair, SEO & AEO Director. You live in Search Console and Ahrefs.
You know what Google's HCU destroyed and what survived. You optimize for both traditional SEO and AI citation (AEO).
You translate every strategy idea into: what keywords, what structure, what timeline.
You are realistic about how long SEO takes and optimistic about AEO opportunities.
Keep responses to 3-4 sentences max. Be precise.`
  },
  {
    id: "cm",
    name: "Sofia Andrade",
    title: "Country Manager — Global",
    avatar: "◇",
    color: "#c95a8f",
    bg: "#1a0812",
    personality: `You are Sofia Andrade, Global Country Manager. You've launched content sites in 15 countries.
You know that Brazil in Portuguese for parenting is a blue ocean. You know German users need TÜV safety signals.
You flag when a strategy will fail culturally or legally in a specific market.
You always bring the multi-market perspective — don't just think in Spain.
Keep responses to 3-4 sentences max. Be specific about markets.`
  },
  {
    id: "ideas",
    name: "Kai Tanaka",
    title: "Chief Innovation Officer",
    avatar: "△",
    color: "#c9a05a",
    bg: "#1a1408",
    personality: `You are Kai Tanaka, Chief Innovation Officer. You only pitch ideas with proven revenue analogues.
You are pragmatic — every idea comes with a proof case, cost estimate, and kill condition.
You push the board to think beyond basic affiliate and toward comparison engines, courses, communities.
You challenge when the board is too conservative or too risk-averse.
Keep responses to 3-4 sentences max. Be bold but evidence-based.`
  },
  {
    id: "audit",
    name: "Elena Kovacs",
    title: "Chief Risk & Quality Officer",
    avatar: "△",
    color: "#a05ac9",
    bg: "#140a1a",
    personality: `You are Elena Kovacs, Chief Risk & Quality Officer. You audit everything.
You spot when skills are outdated, when commission rates have changed, when Google algo shifts threaten the plan.
You bring up what could go wrong. You recommend kill conditions and checkpoints.
You are the voice of "but what if this fails" — essential for sustainable growth.
Keep responses to 3-4 sentences max. Be cautionary but constructive.`
  }
];

const AGENDA_ITEMS = [
  { id: "brand", label: "🏷️ Brand: Is AURUM right or do we need alternatives?", q: "We have AURUM as our brand. Should this be a single multi-vertical brand, or separate brands per niche? Consider the parenting vertical specifically — should it be AURUM Parenting or a standalone brand like 'Nido' or 'Sprout'?" },
  { id: "parenting", label: "👶 Parenting niche: opportunity & strategy", q: "We want to enter the parenting and newborn niche, including baby gear, courses, and childcare. What's our market entry strategy, what are the highest-ROI sub-verticals, and which markets should we target first?" },
  { id: "markets", label: "🌍 Which markets to prioritize first?", q: "We plan to publish in multiple languages. Given our resources (one founder, AI-powered production), which 3-5 markets should we enter first and in what order?" },
  { id: "revenue", label: "💰 Revenue model beyond basic affiliate", q: "Beyond standard affiliate links, what revenue streams should we build in year 1? Consider courses, newsletter, comparison tools, communities." },
  { id: "risk", label: "⚠️ Biggest risks and how to mitigate them", q: "What are the 3 biggest threats to this business and what concrete steps do we take now to mitigate each?" },
];

async function getBoardResponse(member, topic, history) {
  const contextMessages = history.slice(-8).map(m => ({
    role: m.role,
    content: m.content
  }));

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 300,
      system: member.personality,
      messages: [
        ...contextMessages,
        { role: "user", content: `Board topic: "${topic}". Give your expert perspective. Be direct and specific. 3-4 sentences max.` }
      ]
    })
  });
  const data = await res.json();
  return data.content[0].text;
}

async function getSynthesis(topic, boardInput) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 400,
      system: `You are the board secretary. Synthesize a board discussion into a clear executive summary for the CEO.
Format as:
**CONSENSUS:** (what the board agrees on)
**DEBATE:** (where they disagree)  
**DECISION NEEDED:** (what the CEO must decide, with 2-3 concrete options)`,
      messages: [{
        role: "user",
        content: `Topic: ${topic}\n\nBoard input:\n${boardInput}`
      }]
    })
  });
  const data = await res.json();
  return data.content[0].text;
}

function Avatar({ member, size = 40, pulse = false }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: member.bg, border: `2px solid ${member.color}`,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: size * 0.4, color: member.color, flexShrink: 0,
      animation: pulse ? "pulse 1.5s ease-in-out infinite" : "none",
      boxShadow: pulse ? `0 0 12px ${member.color}60` : "none"
    }}>
      {member.avatar}
    </div>
  );
}

function TypingDots({ color }) {
  return (
    <div style={{ display: "flex", gap: "4px", padding: "4px 0" }}>
      {[0,1,2].map(i => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: "50%", background: color,
          animation: `shimmer 1.2s ease-in-out ${i*0.2}s infinite`
        }} />
      ))}
    </div>
  );
}

export default function App() {
  const [phase, setPhase] = useState("lobby"); // lobby | meeting | synthesis
  const [selectedAgenda, setSelectedAgenda] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(null);
  const [synthesis, setSynthesis] = useState(null);
  const [ceoInput, setCeoInput] = useState("");
  const [running, setRunning] = useState(false);
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  async function startMeeting(agendaItem) {
    setSelectedAgenda(agendaItem);
    setMessages([]);
    setSynthesis(null);
    setPhase("meeting");
    setRunning(true);

    const history = [];
    const newMessages = [];

    // Each board member speaks in sequence
    for (const member of BOARD) {
      setTyping(member.id);
      await new Promise(r => setTimeout(r, 600));

      try {
        const response = await getBoardResponse(member, agendaItem.q, history);
        const msg = { id: Date.now() + member.id, role: "assistant", memberId: member.id, content: response };
        newMessages.push(msg);
        history.push({ role: "user", content: `[${member.name}]: ${response}` });
        setMessages([...newMessages]);
        setTyping(null);
        await new Promise(r => setTimeout(r, 400));
      } catch (e) {
        setTyping(null);
      }
    }

    // Generate synthesis
    setTyping("synthesis");
    const boardInput = newMessages.map(m => {
      const member = BOARD.find(b => b.id === m.memberId);
      return `${member.name} (${member.title}): ${m.content}`;
    }).join("\n\n");

    const synth = await getSynthesis(agendaItem.q, boardInput);
    setSynthesis(synth);
    setTyping(null);
    setRunning(false);
  }

  async function ceoChallenges() {
    if (!ceoInput.trim() || running) return;
    setRunning(true);

    const userMsg = { id: Date.now(), role: "user", content: `[CEO]: ${ceoInput}` };
    setMessages(prev => [...prev, userMsg]);
    setCeoInput("");

    // Pick 2-3 relevant board members to respond
    const respondents = BOARD.sort(() => 0.5 - Math.random()).slice(0, 3);

    for (const member of respondents) {
      setTyping(member.id);
      await new Promise(r => setTimeout(r, 800));
      try {
        const history = messages.concat(userMsg).map(m => ({
          role: m.memberId ? "assistant" : "user",
          content: m.content
        }));
        const response = await getBoardResponse(member, ceoInput, history);
        setMessages(prev => [...prev, { id: Date.now() + member.id, role: "assistant", memberId: member.id, content: response }]);
        setTyping(null);
        await new Promise(r => setTimeout(r, 400));
      } catch (e) {
        setTyping(null);
      }
    }
    setRunning(false);
  }

  return (
    <div style={{ background: "#0a0a0a", minHeight: "100vh", fontFamily: "'DM Sans', system-ui, sans-serif", color: "#f0ebe0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=DM+Sans:wght@300;400;500;600&display=swap');
        * { box-sizing: border-box; }
        @keyframes shimmer { 0%,100%{opacity:0.3} 50%{opacity:1} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{box-shadow:0 0 8px currentColor} 50%{box-shadow:0 0 20px currentColor} }
        textarea:focus { outline: none; }
        textarea { resize: none; }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(10,10,10,0.95)", backdropFilter: "blur(10px)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", color: "#d4a853", letterSpacing: "4px" }}>AURUM</div>
          <div style={{ width: "1px", height: "20px", background: "rgba(255,255,255,0.1)" }} />
          <div style={{ fontSize: "12px", color: "#5a5040", letterSpacing: "2px" }}>BOARD ROOM</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {BOARD.map(m => (
            <div key={m.id} title={`${m.name} · ${m.title}`} style={{
              width: 28, height: 28, borderRadius: "50%", background: m.bg,
              border: `1.5px solid ${m.color}40`, display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: "10px", color: m.color, cursor: "default",
              transition: "border-color 0.2s",
              borderColor: typing === m.id ? m.color : `${m.color}40`
            }}>{m.avatar}</div>
          ))}
        </div>
      </div>

      {/* LOBBY */}
      {phase === "lobby" && (
        <div style={{ maxWidth: "720px", margin: "0 auto", padding: "48px 24px" }}>
          <div style={{ animation: "fadeUp 0.6s ease forwards" }}>
            <div style={{ fontSize: "11px", color: "#d4a853", letterSpacing: "3px", marginBottom: "16px" }}>◈ STRATEGIC BOARD MEETING</div>
            <h1 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "clamp(32px,5vw,52px)", fontWeight: "300", lineHeight: "1.1", marginBottom: "12px" }}>
              Your board of<br /><em style={{ color: "#d4a853" }}>expert advisors</em><br />awaits.
            </h1>
            <p style={{ fontSize: "14px", color: "#7a7060", marginBottom: "40px", lineHeight: "1.7", maxWidth: "480px" }}>
              Six AI experts — each with a distinct perspective — will debate your strategic questions. You ask, they challenge each other, you decide.
            </p>

            {/* Board members */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "40px" }}>
              {BOARD.map(m => (
                <div key={m.id} style={{ background: "#141414", border: "1px solid rgba(255,255,255,0.05)", padding: "16px", borderRadius: "4px", display: "flex", gap: "12px", alignItems: "center" }}>
                  <Avatar member={m} size={36} />
                  <div>
                    <div style={{ fontSize: "13px", fontWeight: "600", color: "#e0d8c8" }}>{m.name}</div>
                    <div style={{ fontSize: "11px", color: "#5a5040" }}>{m.title}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Agenda */}
            <div style={{ fontSize: "11px", color: "#5a5040", letterSpacing: "2px", marginBottom: "16px" }}>SELECT AGENDA ITEM</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {AGENDA_ITEMS.map(item => (
                <button key={item.id} onClick={() => startMeeting(item)}
                  style={{
                    background: "#141414", border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: "4px", padding: "16px 20px", textAlign: "left",
                    cursor: "pointer", color: "#c0b8a8", fontSize: "14px",
                    transition: "all 0.2s", display: "flex", justifyContent: "space-between", alignItems: "center"
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "#d4a853"; e.currentTarget.style.color = "#f0ebe0"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)"; e.currentTarget.style.color = "#c0b8a8"; }}>
                  <span>{item.label}</span>
                  <span style={{ color: "#d4a853", fontSize: "16px" }}>→</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MEETING */}
      {phase === "meeting" && (
        <div style={{ maxWidth: "760px", margin: "0 auto", padding: "24px" }}>
          {/* Topic header */}
          <div style={{ background: "#141414", border: "1px solid rgba(212,168,83,0.15)", borderRadius: "4px", padding: "16px 20px", marginBottom: "24px" }}>
            <div style={{ fontSize: "10px", color: "#d4a853", letterSpacing: "2px", marginBottom: "6px" }}>ON THE AGENDA</div>
            <div style={{ fontSize: "14px", color: "#e0d8c8", lineHeight: "1.5" }}>{selectedAgenda?.q}</div>
          </div>

          {/* Messages */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
            {messages.map(msg => {
              const member = BOARD.find(b => b.id === msg.memberId);
              const isCeo = !msg.memberId;
              if (isCeo) return (
                <div key={msg.id} style={{ animation: "fadeUp 0.4s ease forwards", display: "flex", justifyContent: "flex-end" }}>
                  <div style={{ background: "#1a1a1a", border: "1px solid rgba(212,168,83,0.2)", borderRadius: "4px 4px 0 4px", padding: "12px 16px", maxWidth: "80%" }}>
                    <div style={{ fontSize: "10px", color: "#d4a853", letterSpacing: "1.5px", marginBottom: "6px" }}>YOU (CEO)</div>
                    <div style={{ fontSize: "14px", color: "#e0d8c8", lineHeight: "1.6" }}>{msg.content.replace("[CEO]: ", "")}</div>
                  </div>
                </div>
              );
              return (
                <div key={msg.id} style={{ animation: "fadeUp 0.4s ease forwards", display: "flex", gap: "12px" }}>
                  <Avatar member={member} size={38} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: "8px", alignItems: "baseline", marginBottom: "6px" }}>
                      <span style={{ fontSize: "13px", fontWeight: "600", color: member.color }}>{member.name}</span>
                      <span style={{ fontSize: "11px", color: "#5a5040" }}>{member.title}</span>
                    </div>
                    <div style={{ background: "#141414", border: `1px solid ${member.color}20`, borderRadius: "0 4px 4px 4px", padding: "12px 16px" }}>
                      <div style={{ fontSize: "14px", color: "#e0d8c8", lineHeight: "1.7" }}>{msg.content}</div>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Typing indicator */}
            {typing && typing !== "synthesis" && (() => {
              const m = BOARD.find(b => b.id === typing);
              return m ? (
                <div style={{ display: "flex", gap: "12px", animation: "fadeUp 0.3s ease forwards" }}>
                  <Avatar member={m} size={38} pulse />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "13px", color: m.color, marginBottom: "6px" }}>{m.name}</div>
                    <div style={{ background: "#141414", border: `1px solid ${m.color}20`, borderRadius: "0 4px 4px 4px", padding: "12px 16px", display: "inline-block" }}>
                      <TypingDots color={m.color} />
                    </div>
                  </div>
                </div>
              ) : null;
            })()}

            {/* Synthesis */}
            {typing === "synthesis" && (
              <div style={{ background: "#1a1208", border: "1px solid rgba(212,168,83,0.2)", borderRadius: "4px", padding: "16px", animation: "fadeUp 0.3s ease forwards" }}>
                <div style={{ fontSize: "10px", color: "#d4a853", letterSpacing: "2px", marginBottom: "8px" }}>◈ BOARD SECRETARY SYNTHESIZING...</div>
                <TypingDots color="#d4a853" />
              </div>
            )}

            {synthesis && (
              <div style={{ background: "#1a1208", border: "1px solid rgba(212,168,83,0.3)", borderRadius: "4px", padding: "20px", animation: "fadeUp 0.4s ease forwards" }}>
                <div style={{ fontSize: "10px", color: "#d4a853", letterSpacing: "2px", marginBottom: "12px" }}>◈ BOARD SYNTHESIS — FOR CEO DECISION</div>
                <div style={{ fontSize: "14px", color: "#e0d8c8", lineHeight: "1.8", whiteSpace: "pre-wrap" }}>{synthesis}</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* CEO Input */}
          {synthesis && !running && (
            <div style={{ background: "#141414", border: "1px solid rgba(212,168,83,0.2)", borderRadius: "4px", padding: "16px", animation: "fadeUp 0.4s ease" }}>
              <div style={{ fontSize: "10px", color: "#d4a853", letterSpacing: "2px", marginBottom: "10px" }}>YOUR RESPONSE AS CEO</div>
              <textarea
                value={ceoInput}
                onChange={e => setCeoInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ceoChallenges(); } }}
                placeholder="Challenge the board, ask for more detail, or make a decision..."
                rows={3}
                style={{ width: "100%", background: "transparent", border: "none", color: "#f0ebe0", fontSize: "14px", lineHeight: "1.6", padding: "0", fontFamily: "inherit" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                <button onClick={() => { setPhase("lobby"); setMessages([]); setSynthesis(null); }}
                  style={{ background: "transparent", border: "none", color: "#5a5040", fontSize: "12px", cursor: "pointer" }}>
                  ← New agenda item
                </button>
                <button onClick={ceoChallenges} disabled={!ceoInput.trim()}
                  style={{ background: ceoInput.trim() ? "#d4a853" : "#2a2820", color: ceoInput.trim() ? "#0a0a0a" : "#5a5040", border: "none", padding: "8px 20px", fontSize: "12px", fontWeight: "700", letterSpacing: "1px", cursor: ceoInput.trim() ? "pointer" : "default", borderRadius: "2px", transition: "all 0.2s" }}>
                  SEND TO BOARD →
                </button>
              </div>
            </div>
          )}

          {running && !synthesis && (
            <div style={{ textAlign: "center", fontSize: "12px", color: "#5a5040", padding: "16px" }}>
              Board members are deliberating...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
