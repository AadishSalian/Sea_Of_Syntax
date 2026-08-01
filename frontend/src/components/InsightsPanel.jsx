import React from 'react';

const InsightsPanel = ({ insights }) => {
  const hasInsights = insights && (insights.talkingPoints || insights.sentiment || insights.summaries);

  return (
    <div className="glass-panel h-full rounded-2xl p-6 flex flex-col relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white tracking-wide">AI Insights</h2>
        <button className="px-3 py-1.5 text-xs font-semibold text-white bg-white/10 rounded-lg hover:bg-white/20 transition-colors border border-white/20">
          AI insights
        </button>
      </div>
      
      <div className="flex flex-col gap-4 overflow-y-auto custom-scrollbar flex-1 pr-2">
        {!hasInsights ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-500 font-medium">No insights generated yet.</p>
          </div>
        ) : (
          <>
            {insights.talkingPoints && (
              <div>
                <h3 className="text-sm font-semibold text-gray-200 mb-2">Key Talking points</h3>
                <ul className="list-disc pl-4 text-xs text-gray-400 space-y-1">
                  {insights.talkingPoints.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {insights.sentiment && (
              <div>
                <h3 className="text-sm font-semibold text-gray-200 mb-2">Sentiment</h3>
                <p className="text-xs text-gray-400">{insights.sentiment}</p>
              </div>
            )}
            
            {insights.summaries && (
              <div>
                <h3 className="text-sm font-semibold text-gray-200 mb-2">Summaries</h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  {insights.summaries}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default InsightsPanel;
