<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB 2026 Player Game Logs</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tabulator/6.2.0/css/tabulator.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tabulator/6.2.0/js/tabulator.min.js"></script>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; }
        .tab-active { border-bottom: 3px solid #1e40af; font-weight: 600; }
        .modal { animation: fadeIn 0.2s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .tabulator .tabulator-cell { text-align: center; }
        .tabulator .tabulator-header .tabulator-col { text-align: center; }
    </style>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen">
    <div class="max-w-7xl mx-auto p-6">
        <h1 class="text-4xl font-bold mb-2">MLB 2026 Player Game Logs</h1>
        <div id="last-updated" class="text-sm text-zinc-400 mb-6"></div>

        <!-- Global Search -->
        <input id="global-search" type="text" placeholder="Search player..." 
               class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-5 py-3 mb-6 text-lg focus:outline-none focus:border-blue-500">

        <!-- Splits Filters -->
        <div class="flex gap-6 mb-6 bg-zinc-900 p-5 rounded-xl">
            <div>
                <label class="text-xs text-zinc-400 block mb-1">Home / Away</label>
                <select id="split-homeaway" onchange="applyFilters()" class="bg-zinc-800 text-white px-4 py-2 rounded-lg border border-zinc-700">
                    <option value="">All Games</option>
                    <option value="Home">Home Only</option>
                    <option value="Away">Away Only</option>
                </select>
            </div>
            <div>
                <label class="text-xs text-zinc-400 block mb-1">Day / Night</label>
                <select id="split-daynight" onchange="applyFilters()" class="bg-zinc-800 text-white px-4 py-2 rounded-lg border border-zinc-700">
                    <option value="">All</option>
                    <option value="day">Day Games</option>
                    <option value="night">Night Games</option>
                </select>
            </div>
        </div>

        <!-- Tabs -->
        <div class="flex border-b border-zinc-700 mb-6">
            <button onclick="switchTab(0)" id="tab-batters" class="tab px-8 py-4 text-lg tab-active">Batters</button>
            <button onclick="switchTab(1)" id="tab-pitchers" class="tab px-8 py-4 text-lg">Pitchers</button>
        </div>

        <div id="table-container" class="bg-zinc-900 rounded-xl overflow-hidden shadow-2xl"></div>
    </div>

    <!-- Player Profile Modal -->
    <div id="profile-modal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center z-50 modal overflow-auto">
        <div class="bg-zinc-900 rounded-3xl w-full max-w-6xl mx-4 my-8 max-h-[92vh] flex flex-col">
            <div class="px-8 py-6 border-b border-zinc-700 flex items-center justify-between">
                <div id="profile-header" class="flex items-center gap-4"></div>
                <button onclick="closeProfileModal()" class="text-4xl text-zinc-400 hover:text-white">×</button>
            </div>
            
            <div class="flex-1 overflow-auto p-8" id="profile-content">
                <!-- Populated by JS -->
            </div>
        </div>
    </div>

    <script>
        let gameLogData = [];
        let perInningData = [];
        let currentTab = 0;
        let table = null;
        let currentPlayerData = null;

        const GAME_LOG_URL = "https://raw.githubusercontent.com/925Sports/mlb-player-game-logs/main/mlb_2026_season_game_logs.csv";
        const PER_INNING_URL = "https://raw.githubusercontent.com/925Sports/mlb-player-game-logs/main/mlb_2026_per_inning_logs.csv";

        async function loadData() {
            const [gameRes, inningRes] = await Promise.all([
                fetch(GAME_LOG_URL + '?t=' + Date.now()),
                fetch(PER_INNING_URL + '?t=' + Date.now())
            ]);

            const gameText = await gameRes.text();
            const inningText = await inningRes.text();

            // Parse game logs
            const gameRows = gameText.trim().split('\n');
            const gameHeaders = gameRows[0].split(',').map(h => h.trim().replace(/"/g, ''));
            gameLogData = gameRows.slice(1).map(row => {
                const values = row.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
                const obj = {};
                gameHeaders.forEach((h, i) => obj[h] = values[i] ? values[i].trim().replace(/"/g, '') : '');
                return obj;
            });

            // Parse per-inning
            const inningRows = inningText.trim().split('\n');
            const inningHeaders = inningRows[0].split(',').map(h => h.trim().replace(/"/g, ''));
            perInningData = inningRows.slice(1).map(row => {
                const values = row.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
                const obj = {};
                inningHeaders.forEach((h, i) => obj[h] = values[i] ? values[i].trim().replace(/"/g, '') : '');
                return obj;
            });

            document.getElementById('last-updated').textContent = `Last updated: ${new Date().toLocaleString()}`;
            buildTable();

            // Global search
            document.getElementById('global-search').addEventListener('input', () => buildTable());
        }

        function getTeamAndResult(row) {
            const homeAbbr = row.home_team_abbreviation || '';
            const awayAbbr = row.away_team_abbreviation || '';
            const isHome = homeAbbr === row.home_team_abbreviation && row.home_team_abbreviation;
            const team = isHome ? homeAbbr : awayAbbr;
            const opponent = isHome ? awayAbbr : homeAbbr;
            const result = `${row.home_isWinner === "True" ? "W" : "L"} ${row.home_score}-${row.away_score}`;
            return { team, opponent: `vs ${opponent}`, result, isHome: isHome ? "Home" : "Away", dayNight: (row.dayNight || "").toLowerCase() };
        }

        function buildTable() {
            const container = document.getElementById('table-container');
            container.innerHTML = '';

            const isBatters = currentTab === 0;
            const searchTerm = document.getElementById('global-search').value.toLowerCase().trim();

            const columns = [
                { title: "Date", field: "gameDate", width: 110, headerFilter: "input", hozAlign: "center" },
                { title: "Player", field: "fullName", width: 220, headerFilter: "input" },
                { title: "Team", field: "team", width: 90, headerFilter: "input", hozAlign: "center" },
                { title: "Opponent", field: "opponent", width: 120, headerFilter: "input", hozAlign: "center" },
                { title: "Result", field: "result", width: 110, hozAlign: "center" },
                { title: "Pos", field: "primaryPosition_name", width: 110, headerFilter: "input", hozAlign: "center" },
            ];

            if (isBatters) {
                columns.push(
                    { title: "AB", field: "atBats", width: 70, hozAlign: "center" },
                    { title: "H", field: "hits", width: 70, hozAlign: "center" },
                    { title: "HR", field: "homeRuns", width: 70, hozAlign: "center" },
                    { title: "RBI", field: "rbi", width: 70, hozAlign: "center" },
                    { title: "R", field: "runs", width: 70, hozAlign: "center" },
                    { title: "K", field: "strikeOuts", width: 70, hozAlign: "center" },
                    { title: "BB", field: "baseOnBalls", width: 70, hozAlign: "center" },
                    { title: "Summary", field: "gameLogSummary", minWidth: 300 }
                );
            } else {
                columns.push(
                    { title: "IP", field: "inningsPitched", width: 80, hozAlign: "center" },
                    { title: "ER", field: "earnedRuns", width: 70, hozAlign: "center" },
                    { title: "H", field: "hitsAllowed", width: 70, hozAlign: "center" },
                    { title: "HR", field: "homeRunsAllowed", width: 70, hozAlign: "center" },
                    { title: "K", field: "strikeOutsPitching", width: 70, hozAlign: "center" },
                    { title: "BB", field: "baseOnBallsPitching", width: 70, hozAlign: "center" },
                    { title: "Pitches", field: "pitchesThrown", width: 90, hozAlign: "center" },
                    { title: "Decision", field: "note", width: 110, hozAlign: "center" },
                    { title: "Summary", field: "gameLogSummary", minWidth: 300 }
                );
            }

            let filteredData = gameLogData.filter(row => {
                if (isBatters) return parseFloat(row.atBats || 0) > 0;
                return parseFloat(row.inningsPitched || 0) > 0 || row.note;
            }).map(row => {
                const extra = getTeamAndResult(row);
                return { ...row, team: extra.team, opponent: extra.opponent, result: extra.result, isHome: extra.isHome, dayNight: extra.dayNight };
            });

            if (searchTerm) {
                filteredData = filteredData.filter(row => 
                    row.fullName.toLowerCase().includes(searchTerm)
                );
            }

            table = new Tabulator("#table-container", {
                data: filteredData,
                columns: columns,
                layout: "fitColumns",
                pagination: "local",
                paginationSize: 50,
                paginationSizeSelector: [25, 50, 100, 250],
                initialSort: [{ column: "gameDate", dir: "desc" }],
                rowClick: (e, row) => showPlayerProfile(row.getData())
            });
        }

        function applyFilters() {
            if (!table) return;
            const homeAway = document.getElementById('split-homeaway').value;
            const dayNight = document.getElementById('split-daynight').value;

            table.setFilter(row => {
                if (homeAway && row.isHome !== homeAway) return false;
                if (dayNight && row.dayNight !== dayNight) return false;
                return true;
            });
        }

        function showPlayerProfile(rowData) {
            currentPlayerData = rowData;
            const modal = document.getElementById('profile-modal');
            const header = document.getElementById('profile-header');
            const content = document.getElementById('profile-content');

            header.innerHTML = `
                <div class="text-3xl font-bold">${rowData.fullName}</div>
                <div class="text-xl text-zinc-400">${rowData.primaryPosition_name} • ${rowData.team}</div>
            `;

            // Calculate season stats
            const playerRows = gameLogData.filter(r => r.playerId === rowData.playerId);
            const isBatter = parseFloat(rowData.atBats || 0) > 0;

            let statsHTML = '';
            if (isBatter) {
                const totalAB = playerRows.reduce((a, r) => a + parseFloat(r.atBats || 0), 0);
                const totalH = playerRows.reduce((a, r) => a + parseFloat(r.hits || 0), 0);
                statsHTML = `AVG: ${(totalH / totalAB || 0).toFixed(3)} • HR: ${playerRows.reduce((a, r) => a + parseFloat(r.homeRuns || 0), 0)}`;
            } else {
                const totalIP = playerRows.reduce((a, r) => a + parseFloat(r.inningsPitched || 0), 0);
                statsHTML = `ERA: ${((playerRows.reduce((a, r) => a + parseFloat(r.earnedRuns || 0), 0) / totalIP) * 9 || 0).toFixed(2)} • K: ${playerRows.reduce((a, r) => a + parseFloat(r.strikeOutsPitching || 0), 0)}`;
            }

            content.innerHTML = `
                <div class="grid grid-cols-2 gap-8">
                    <div>
                        <h3 class="text-xl font-semibold mb-4">Player Bio</h3>
                        <div class="space-y-3 text-lg">
                            <p><span class="text-zinc-400">Age:</span> ${rowData.currentAge || 'N/A'}</p>
                            <p><span class="text-zinc-400">Height:</span> ${rowData.height || 'N/A'}</p>
                            <p><span class="text-zinc-400">Weight:</span> ${rowData.weight || 'N/A'}</p>
                            <p><span class="text-zinc-400">Born:</span> ${rowData.birthDate || 'N/A'}</p>
                            <p><span class="text-zinc-400">Bats:</span> ${rowData.batSide_description || 'N/A'}</p>
                            <p><span class="text-zinc-400">Throws:</span> ${rowData.pitchHand_description || 'N/A'}</p>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-xl font-semibold mb-4">Season Averages</h3>
                        <div class="text-2xl">${statsHTML}</div>
                    </div>
                </div>

                <h3 class="text-xl font-semibold mt-8 mb-4">Splits</h3>
                <div class="grid grid-cols-2 gap-6">
                    <div class="bg-zinc-800 p-4 rounded-2xl">Home: ${playerRows.filter(r => getTeamAndResult(r).isHome === "Home").length} games</div>
                    <div class="bg-zinc-800 p-4 rounded-2xl">Away: ${playerRows.filter(r => getTeamAndResult(r).isHome === "Away").length} games</div>
                </div>

                <h3 class="text-xl font-semibold mt-8 mb-4">Per-Inning Details</h3>
                <div id="per-inning-in-profile" class="max-h-96 overflow-auto"></div>
            `;

            // Per-inning inside profile
            const detailsContainer = document.getElementById('per-inning-in-profile');
            const details = perInningData.filter(p => 
                String(p.gamePk) === String(rowData.gamePk) && 
                (isBatter 
                    ? String(p.batterId || p.playerId) === String(rowData.playerId)
                    : String(p.pitcherId || p.playerId) === String(rowData.playerId))
            );

            let html = `<table class="w-full text-sm"><thead class="bg-zinc-800"><tr><th class="p-3">Inning</th><th class="p-3">Result</th><th class="p-3">Description</th><th class="p-3">Pitches</th></tr></thead><tbody>`;
            details.forEach(d => {
                html += `<tr class="border-t"><td class="p-3">${d.inning}</td><td class="p-3">${d.atBatResult || d.event}</td><td class="p-3">${d.description}</td><td class="p-3">${d.pitchesInAB || ''}</td></tr>`;
            });
            html += `</tbody></table>`;
            detailsContainer.innerHTML = html || '<p class="text-zinc-400">No per-inning data available for this game.</p>';

            modal.classList.remove('hidden');
        }

        function closeProfileModal() {
            document.getElementById('profile-modal').classList.add('hidden');
        }

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tab-batters').classList.toggle('tab-active', tab === 0);
            document.getElementById('tab-pitchers').classList.toggle('tab-active', tab === 1);
            buildTable();
        }

        window.onload = loadData;
    </script>
</body>
</html>
