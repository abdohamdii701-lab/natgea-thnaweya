import os

cf_worker_code = """export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle CORS Preflight OPTIONS requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': '*',
        }
      });
    }

    // 1. Dynamic API Endpoint: Search Tracking Ping
    if (url.pathname === '/api/search_ping') {
      const q = url.searchParams.get('q') || '';
      const mode = url.searchParams.get('mode') || 'auto';
      const ip = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '127.0.0.1';
      const ua = request.headers.get('user-agent') || 'Browser';
      const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

      if (q) {
        if (!globalThis.CF_SEARCH_LOGS) {
          globalThis.CF_SEARCH_LOGS = [
            { ip: '156.204.88.12', query: '2001970', mode: 'seating', user_agent: 'Mobile Safari', timestamp: timestamp },
            { ip: '41.234.12.89', query: 'محمد علي', mode: 'name', user_agent: 'Chrome Windows', timestamp: timestamp }
          ];
        }

        globalThis.CF_SEARCH_LOGS.unshift({
          ip: ip,
          query: q,
          mode: mode,
          user_agent: ua,
          timestamp: timestamp
        });

        // Limit memory queue to 300 logs
        if (globalThis.CF_SEARCH_LOGS.length > 300) {
          globalThis.CF_SEARCH_LOGS = globalThis.CF_SEARCH_LOGS.slice(0, 300);
        }
      }

      return new Response(JSON.stringify({ status: 'logged' }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': '*'
        }
      });
    }

    // 2. Dynamic API Endpoint: Admin Logs
    if (url.pathname === '/api/admin/logs') {
      const key = url.searchParams.get('key');
      if (key !== 'admin123') {
        return new Response(JSON.stringify({ error: 'Unauthorized - Wrong Key' }), {
          status: 401,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      const logs = globalThis.CF_SEARCH_LOGS || [
        { ip: '156.204.88.12', query: '2001970', mode: 'seating', user_agent: 'Mobile Safari', timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) },
        { ip: '41.234.12.89', query: 'محمد علي', mode: 'name', user_agent: 'Chrome Windows', timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) }
      ];

      const total = logs.length;
      const uniqueIps = new Set(logs.map(l => l.ip)).size;
      const todayStr = new Date().toISOString().slice(0, 10);
      const todayCount = logs.filter(l => l.timestamp.startsWith(todayStr)).length;

      const counts = {};
      logs.forEach(l => {
        counts[l.query] = (counts[l.query] || 0) + 1;
      });

      const topQueries = Object.keys(counts)
        .map(q => ({ query: q, count: counts[q], last_time: '' }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

      const topQueryName = topQueries.length ? topQueries[0].query : '—';

      return new Response(JSON.stringify({
        total_searches: total,
        unique_ips: uniqueIps,
        today_searches: todayCount,
        top_query: topQueryName,
        top_queries: topQueries,
        logs: logs
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': '*'
        }
      });
    }

    // 3. Serve Static Assets (HTML, CSS, JS, JSON) from Cloudflare Assets
    return env.ASSETS.fetch(request);
  }
};
"""

# Write to dist/_worker.js for Cloudflare Pages / Workers deployment
dist_worker_path = 'dist/_worker.js'
with open(dist_worker_path, 'w', encoding='utf-8') as f:
    f.write(cf_worker_code)

print(f"Created Cloudflare Worker script at {dist_worker_path}")
