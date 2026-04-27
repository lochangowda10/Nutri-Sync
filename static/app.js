/* ======================================================
   NutriSync v2 — SPA Controller
   ====================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // === State ===
    let selectedFood = null;
    let selectedReason = null;
    let healthChart = null;
    let weeklyChart = null;

    // === DOM References ===
    const navLinks = document.querySelectorAll('.nav-link');
    const tabs = document.querySelectorAll('.tab-content');
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');

    // === Navigation ===
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = link.dataset.tab;
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            tabs.forEach(t => t.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            sidebar.classList.remove('open');
            if (tabId === 'dashboard') refreshDashboard();
            if (tabId === 'report') loadWeeklyReport();
            if (tabId === 'streaks') loadStreaks();
        });
    });

    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

    // === Initialization ===
    initGreeting();
    loadEatingReasons();
    initFoodSearch();
    initSubstituteSearch();
    refreshDashboard();

    // ==========================================
    // GREETING
    // ==========================================
    function initGreeting() {
        const h = new Date().getHours();
        const el = document.getElementById('greeting-time');
        if (h < 12) el.textContent = 'Morning';
        else if (h < 17) el.textContent = 'Afternoon';
        else el.textContent = 'Evening';
    }

    // ==========================================
    // LOCAL STORAGE HELPERS
    // ==========================================
    function getMealHistory() {
        try { return JSON.parse(localStorage.getItem('nutrisync_meals') || '[]'); }
        catch { return []; }
    }

    function saveMeal(meal) {
        const history = getMealHistory();
        history.push(meal);
        localStorage.setItem('nutrisync_meals', JSON.stringify(history));
    }

    function getTodayMeals() {
        const today = new Date().toISOString().split('T')[0];
        return getMealHistory().filter(m => m.date === today);
    }

    function getTodayTotals() {
        const meals = getTodayMeals();
        return {
            calories: meals.reduce((s, m) => s + (m.calories || 0), 0),
            protein: meals.reduce((s, m) => s + (m.protein || 0), 0),
            sugar: meals.reduce((s, m) => s + (m.sugar || 0), 0),
            count: meals.length,
        };
    }

    // ==========================================
    // DASHBOARD
    // ==========================================
    function refreshDashboard() {
        const totals = getTodayTotals();

        document.getElementById('dash-calories').textContent = totals.calories;
        document.getElementById('dash-protein').textContent = totals.protein + 'g';
        document.getElementById('dash-sugar').textContent = totals.sugar + 'g';
        document.getElementById('dash-meals').textContent = totals.count;

        document.getElementById('cal-bar').style.width = Math.min(totals.calories / 2000 * 100, 100) + '%';
        document.getElementById('protein-bar').style.width = Math.min(totals.protein / 50 * 100, 100) + '%';
        document.getElementById('sugar-bar').style.width = Math.min(totals.sugar / 40 * 100, 100) + '%';
        document.getElementById('meals-bar').style.width = Math.min(totals.count / 5 * 100, 100) + '%';

        renderTodayMeals();
        renderHealthChart();
        updateNudge(totals);
    }

    function renderTodayMeals() {
        const meals = getTodayMeals();
        const container = document.getElementById('today-meals-list');
        if (!meals.length) {
            container.innerHTML = '<p class="empty-state">No meals logged yet. Start by logging your first meal! 🍽️</p>';
            return;
        }
        container.innerHTML = meals.map(m => {
            const scoreClass = m.health_score >= 7 ? 'score-good' : m.health_score >= 5 ? 'score-ok' : 'score-bad';
            return `<div class="meal-entry">
                <div><span class="meal-name">${m.food_name}</span><br><span class="meal-cal">${m.calories} cal · ${m.protein}g protein</span></div>
                <span class="meal-score ${scoreClass}">${m.health_score}/10</span>
            </div>`;
        }).join('');
    }

    function renderHealthChart() {
        const history = getMealHistory().slice(-20);
        const labels = history.map((_, i) => 'Meal ' + (i + 1));
        const scores = history.map(m => m.health_score || 5);

        const ctx = document.getElementById('healthChart');
        if (healthChart) healthChart.destroy();
        healthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Health Score',
                    data: scores,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16,185,129,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { min: 0, max: 10, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 8 } }
                }
            }
        });
    }

    function updateNudge(totals) {
        const el = document.getElementById('nudge-text');
        const h = new Date().getHours();
        if (totals.count === 0 && h < 11) {
            el.textContent = "🌅 Don't skip breakfast! It sets the tone for your whole day. Log your first meal now.";
        } else if (totals.sugar > 35) {
            el.textContent = "🍬 You're close to your sugar limit today. Consider water or green tea for your next drink.";
        } else if (totals.protein < 20 && h > 15) {
            el.textContent = "💪 Your protein is low today. Consider adding eggs, paneer, or dal to your next meal.";
        } else if (totals.count >= 4) {
            el.textContent = "📊 You've logged " + totals.count + " meals today. Great tracking! Keep being mindful.";
        } else if (h >= 21) {
            el.textContent = "🌙 It's late. If you're hungry, choose something light like curd rice or fruit.";
        } else {
            el.textContent = "Welcome to NutriSync! Log your meals to get AI-powered insights about your eating patterns.";
        }
    }

    // ==========================================
    // FOOD SEARCH & LOG MEAL
    // ==========================================
    function initFoodSearch() {
        const input = document.getElementById('food-search');
        const results = document.getElementById('search-results');
        let debounce;

        input.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(async () => {
                const q = input.value.trim();
                if (q.length < 2) { results.classList.remove('show'); return; }
                try {
                    const res = await fetch('/api/search-foods', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: q })
                    });
                    const data = await res.json();
                    if (data.results.length) {
                        results.innerHTML = data.results.map(f =>
                            `<div class="search-item" data-name="${f.name}">
                                <span class="food-name">${f.name}</span>
                                <span class="food-meta">${f.calories} cal · ${f.category}</span>
                            </div>`
                        ).join('');
                        results.classList.add('show');
                        results.querySelectorAll('.search-item').forEach(item => {
                            item.addEventListener('click', () => {
                                selectedFood = data.results.find(f => f.name === item.dataset.name);
                                input.value = selectedFood.name;
                                results.classList.remove('show');
                                checkFormReady();
                            });
                        });
                    } else {
                        results.innerHTML = '<div class="search-item"><span class="food-name">No results found</span></div>';
                        results.classList.add('show');
                    }
                } catch (e) { console.error(e); }
            }, 250);
        });

        input.addEventListener('blur', () => setTimeout(() => results.classList.remove('show'), 200));
    }

    // ==========================================
    // EATING REASONS
    // ==========================================
    async function loadEatingReasons() {
        try {
            const res = await fetch('/api/eating-reasons');
            const data = await res.json();
            const grid = document.getElementById('reasons-grid');
            grid.innerHTML = data.reasons.map(r =>
                `<div class="reason-chip" data-id="${r.id}">
                    <span>${r.emoji}</span><span>${r.label}</span>
                </div>`
            ).join('');
            grid.querySelectorAll('.reason-chip').forEach(chip => {
                chip.addEventListener('click', () => {
                    grid.querySelectorAll('.reason-chip').forEach(c => c.classList.remove('selected'));
                    chip.classList.add('selected');
                    selectedReason = chip.dataset.id;
                    checkFormReady();
                });
            });
        } catch (e) { console.error(e); }
    }

    function checkFormReady() {
        document.getElementById('btn-analyze').disabled = !(selectedFood && selectedReason);
    }

    // ==========================================
    // ANALYZE MEAL
    // ==========================================
    document.getElementById('btn-analyze').addEventListener('click', async () => {
        if (!selectedFood || !selectedReason) return;
        const totals = getTodayTotals();
        const day = new Date().getDay();

        try {
            const res = await fetch('/api/analyze-meal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    food_name: selectedFood.name,
                    eating_reason: selectedReason,
                    today_calories: totals.calories,
                    today_sugar: totals.sugar,
                    today_protein: totals.protein,
                    meals_today: totals.count,
                    is_weekend: day === 0 || day === 6,
                })
            });
            const data = await res.json();
            if (!data.found) {
                alert(data.message);
                return;
            }
            renderAIResponse(data);
        } catch (e) { console.error(e); }
    });

    function renderAIResponse(data) {
        const container = document.getElementById('ai-response');
        container.classList.remove('hidden', 'severity-warning', 'severity-alert');
        if (data.severity === 'warning') container.classList.add('severity-warning');
        if (data.severity === 'alert') container.classList.add('severity-alert');

        const badge = document.getElementById('severity-badge');
        badge.textContent = data.severity === 'good' ? '✅ Good Choice' : data.severity === 'warning' ? '⚠️ Caution' : '🚨 Think Twice';
        badge.className = 'severity-badge severity-' + data.severity;

        const f = data.food;
        document.getElementById('food-summary').innerHTML = `
            <div class="food-stat"><span class="val">${f.calories}</span><span class="lbl">Calories</span></div>
            <div class="food-stat"><span class="val">${f.protein}g</span><span class="lbl">Protein</span></div>
            <div class="food-stat"><span class="val">${f.sugar}g</span><span class="lbl">Sugar</span></div>
            <div class="food-stat"><span class="val">${f.fat}g</span><span class="lbl">Fat</span></div>
            <div class="food-stat"><span class="val">${data.health_score}/10</span><span class="lbl">Score</span></div>
        `;

        document.getElementById('insights-list').innerHTML = data.insights.map(i =>
            `<div class="insight-item">${i}</div>`
        ).join('');

        document.getElementById('subs-inline').classList.add('hidden');
    }

    // ==========================================
    // LOG MEAL (after analysis)
    // ==========================================
    document.getElementById('btn-log-anyway').addEventListener('click', () => {
        if (!selectedFood) return;
        const today = new Date().toISOString().split('T')[0];
        const day = new Date().getDay();
        saveMeal({
            food_name: selectedFood.name,
            calories: selectedFood.calories,
            protein: selectedFood.protein,
            sugar: selectedFood.sugar,
            fat: selectedFood.fat,
            health_score: selectedFood.health_score,
            category: selectedFood.category,
            reason: selectedReason,
            hour: new Date().getHours(),
            date: today,
            is_weekend: day === 0 || day === 6,
        });

        // Reset form
        selectedFood = null;
        selectedReason = null;
        document.getElementById('food-search').value = '';
        document.querySelectorAll('.reason-chip').forEach(c => c.classList.remove('selected'));
        document.getElementById('btn-analyze').disabled = true;
        document.getElementById('ai-response').classList.add('hidden');

        // Show confirmation
        alert('✅ Meal logged! Check your Dashboard for updated stats.');
        refreshDashboard();
    });

    // ==========================================
    // SHOW INLINE SUBSTITUTES
    // ==========================================
    document.getElementById('btn-show-subs').addEventListener('click', async () => {
        if (!selectedFood) return;
        try {
            const res = await fetch('/api/get-substitutes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ food_name: selectedFood.name })
            });
            const data = await res.json();
            const container = document.getElementById('subs-inline');
            container.classList.remove('hidden');
            container.innerHTML = renderSubstitutes(data);
        } catch (e) { console.error(e); }
    });

    // ==========================================
    // SUBSTITUTES TAB
    // ==========================================
    function initSubstituteSearch() {
        const input = document.getElementById('sub-search');
        let debounce;
        input.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(async () => {
                const q = input.value.trim();
                if (q.length < 2) { document.getElementById('sub-results').innerHTML = ''; return; }
                try {
                    const res = await fetch('/api/get-substitutes', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ food_name: q })
                    });
                    const data = await res.json();
                    document.getElementById('sub-results').innerHTML = renderSubstitutes(data);
                } catch (e) { console.error(e); }
            }, 300);
        });
    }

    function renderSubstitutes(data) {
        if (!data.alternatives || !data.alternatives.length) {
            return '<p class="empty-state">No specific substitutes found. Try a different food name.</p>';
        }
        let html = data.alternatives.map(a =>
            `<div class="sub-card">
                <div class="sub-score">${a.health_score}</div>
                <div class="sub-info">
                    <div class="sub-name">${a.name}</div>
                    <div class="sub-meta">${a.calories} cal · ${a.protein}g protein · ${a.sugar}g sugar</div>
                </div>
            </div>`
        ).join('');
        if (data.tip) {
            html += `<div class="sub-tip">💡 <strong>Pro Tip:</strong> ${data.tip}</div>`;
        }
        return html;
    }

    // ==========================================
    // WEEKLY REPORT
    // ==========================================
    async function loadWeeklyReport() {
        const history = getMealHistory();
        try {
            const res = await fetch('/api/weekly-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meal_history: history })
            });
            const data = await res.json();

            // Metrics
            const metricsEl = document.getElementById('report-metrics');
            if (data.metrics) {
                const m = data.metrics;
                metricsEl.innerHTML = `
                    <div class="metric-card"><span class="metric-value green">${m.total_meals}</span><span class="metric-label">Total Meals</span></div>
                    <div class="metric-card"><span class="metric-value blue">${m.avg_health_score}</span><span class="metric-label">Avg Health Score</span></div>
                    <div class="metric-card"><span class="metric-value green">${m.healthy_choices}</span><span class="metric-label">Healthy Choices</span></div>
                    <div class="metric-card"><span class="metric-value red">${m.unhealthy_choices}</span><span class="metric-label">Unhealthy Choices</span></div>
                    <div class="metric-card"><span class="metric-value purple">${m.healthy_pct}%</span><span class="metric-label">Healthy Rate</span></div>
                `;
            }

            // Patterns
            const patternsEl = document.getElementById('report-patterns');
            if (data.patterns && data.patterns.length) {
                patternsEl.innerHTML = data.patterns.map(p =>
                    `<div class="pattern-item">${p}</div>`
                ).join('');
            } else {
                patternsEl.innerHTML = '<p class="empty-state">Log meals for a few days to generate your AI behavior report.</p>';
            }

            // Chart
            renderWeeklyChart(history);
        } catch (e) { console.error(e); }
    }

    function renderWeeklyChart(history) {
        const days = {};
        history.forEach(m => {
            if (!days[m.date]) days[m.date] = { cal: 0, protein: 0, sugar: 0 };
            days[m.date].cal += m.calories || 0;
            days[m.date].protein += m.protein || 0;
            days[m.date].sugar += m.sugar || 0;
        });
        const labels = Object.keys(days).slice(-7);
        const calData = labels.map(d => days[d].cal);
        const proteinData = labels.map(d => days[d].protein);
        const sugarData = labels.map(d => days[d].sugar);

        const ctx = document.getElementById('weeklyChart');
        if (weeklyChart) weeklyChart.destroy();
        weeklyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.map(d => d.slice(5)),
                datasets: [
                    { label: 'Calories', data: calData, backgroundColor: 'rgba(16,185,129,0.6)' },
                    { label: 'Protein (g)', data: proteinData, backgroundColor: 'rgba(59,130,246,0.6)' },
                    { label: 'Sugar (g)', data: sugarData, backgroundColor: 'rgba(245,158,11,0.6)' },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b' } }
                }
            }
        });
    }

    // ==========================================
    // STREAKS
    // ==========================================
    async function loadStreaks() {
        const history = getMealHistory();
        try {
            const res = await fetch('/api/calculate-streaks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meal_history: history })
            });
            const data = await res.json();
            const grid = document.getElementById('streaks-grid');
            if (data.streaks && data.streaks.length) {
                grid.innerHTML = data.streaks.map(s =>
                    `<div class="streak-card">
                        <div class="streak-emoji">${s.emoji}</div>
                        <div class="streak-name">${s.name}</div>
                        <div class="streak-desc">${s.description}</div>
                        <div class="streak-count">${s.current}</div>
                        <div class="streak-label">day streak</div>
                        <div class="streak-best">🏆 Best: ${s.best} days</div>
                    </div>`
                ).join('');
            }

            // Impact metrics
            const totalMeals = history.length;
            const healthy = history.filter(m => (m.health_score || 5) >= 7).length;
            const unhealthy = history.filter(m => (m.health_score || 5) <= 4).length;
            const avgScore = totalMeals ? (history.reduce((s, m) => s + (m.health_score || 5), 0) / totalMeals).toFixed(1) : '—';

            document.getElementById('impact-grid').innerHTML = `
                <div class="impact-item"><span class="impact-val green">${healthy}</span><span class="impact-lbl">Healthy Decisions</span></div>
                <div class="impact-item"><span class="impact-val red">${unhealthy}</span><span class="impact-lbl">Unhealthy Reduced</span></div>
                <div class="impact-item"><span class="impact-val blue">${avgScore}</span><span class="impact-lbl">Avg Health Score</span></div>
                <div class="impact-item"><span class="impact-val purple">${totalMeals}</span><span class="impact-lbl">Total Logged</span></div>
            `;
        } catch (e) { console.error(e); }
    }

});
