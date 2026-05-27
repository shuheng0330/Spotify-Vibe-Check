import { LineChart, Network, BookOpen, Music, Mic2, MapPin, BarChart3 } from 'lucide-react';

export default function MainTab() {
  const steps = [
    {
      number: '01',
      icon: Mic2,
      title: 'Describe Your Vibe',
      description:
        'Head to the Vibe Check tab and chat with the Dynamic DJ agent. Tell it how you feel — "chill Sunday morning", "high-energy workout", or anything in between. The agent will interpret your mood and map it to audio features.',
    },
    {
      number: '02',
      icon: MapPin,
      title: 'Get Your Cluster & Playlist',
      description:
        'The agent finds the best-matching cluster in the latent audio space using PCA + K-Means, then generates a personalised playlist from that cluster. You can save the playlist to your library for later.',
    },
    {
      number: '03',
      icon: BarChart3,
      title: 'Explore & Analyse',
      description:
        'Visit Explore Clusters to visualise how all song clusters relate to each other in 2-D space. Switch to Academic Analysis for a comparative feature matrix, silhouette scores, and algorithm benchmarks.',
    },
  ];

  const features = [
    { icon: LineChart, label: 'Vibe Check', desc: 'Conversational DJ agent' },
    { icon: Network, label: 'Explore Clusters', desc: '2-D audio latent space' },
    { icon: BookOpen, label: 'Academic Analysis', desc: 'ML algorithm benchmarks' },
    { icon: Music, label: 'Saved Playlists', desc: 'Your personal library' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-10 py-4">
      {/* Hero */}
      <div className="glass-panel rounded-2xl p-8 border border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#53e076]/5 rounded-full blur-3xl -z-10" />
        <div className="flex items-center gap-3 mb-4">
          <span className="w-10 h-10 rounded-xl bg-[#1db954] flex items-center justify-center font-black text-black text-base">VC</span>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight">Spotify Vibe Check</h1>
            <p className="text-xs text-[#53e076] font-semibold uppercase tracking-widest">
              Unsupervised Audio-Feature Clustering · Conversational DJ Agent
            </p>
          </div>
        </div>
        <p className="text-sm text-[#bccbb9] leading-relaxed max-w-2xl">
          Vibe Check is a machine-learning music analytics platform. It clusters ~114 000 Spotify tracks
          by their audio features using PCA dimensionality reduction and K-Means / GMM competitive
          selection, then exposes those clusters through a conversational DJ agent powered by OpenRouter.
          Describe how you feel and let the agent build the perfect playlist.
        </p>
      </div>

      {/* How to use */}
      <div>
        <h2 className="text-xs text-[#bccbb9] uppercase tracking-widest font-bold mb-5">How to use</h2>
        <div className="space-y-4">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.number}
                className="glass-panel rounded-xl p-6 border border-white/10 flex gap-5 items-start"
              >
                <div className="flex-shrink-0 flex flex-col items-center gap-2">
                  <span className="text-[10px] font-black text-[#53e076] tracking-widest">{step.number}</span>
                  <span className="w-9 h-9 rounded-lg bg-[#53e076]/10 border border-[#53e076]/20 flex items-center justify-center">
                    <Icon size={16} className="text-[#53e076]" />
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white mb-1">{step.title}</h3>
                  <p className="text-xs text-[#bccbb9] leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Feature grid */}
      <div>
        <h2 className="text-xs text-[#bccbb9] uppercase tracking-widest font-bold mb-5">Pages at a glance</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.label}
                className="glass-panel rounded-xl p-4 border border-white/10 flex flex-col items-center text-center gap-2"
              >
                <span className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                  <Icon size={16} className="text-[#53e076]" />
                </span>
                <span className="text-xs font-bold text-white">{f.label}</span>
                <span className="text-[10px] text-[#bccbb9]">{f.desc}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tech stack note */}
      <div className="glass-panel rounded-xl p-5 border border-white/10 text-[10px] text-[#bccbb9] leading-relaxed">
        <span className="text-[#53e076] font-bold uppercase tracking-wider">Tech stack — </span>
        React + Tailwind (frontend) · FastAPI (backend) · scikit-learn PCA / K-Means / GMM / DBSCAN ·
        OpenRouter GLM-4.5 (DJ agent) · Spotipy (playlist enrichment) · Pollinations.ai (album art)
      </div>
    </div>
  );
}
