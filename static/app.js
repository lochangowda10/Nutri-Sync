document.addEventListener('DOMContentLoaded', () => {
    const btnLocate = document.getElementById('btn-locate');
    const btnDemo = document.getElementById('btn-demo');
    const btnReset = document.getElementById('btn-reset');
    
    const locationCard = document.querySelector('.location-card');
    const loadingState = document.getElementById('loading-state');
    const resultCard = document.getElementById('result-card');
    const statusMessage = document.getElementById('location-status');
    
    const fatigueLevelEl = document.getElementById('fatigue-level');
    const fatigueReasonEl = document.getElementById('fatigue-reason');
    const recommendationTextEl = document.getElementById('recommendation-text');

    const API_URL = '/api/evaluate';

    // Auto-Locate User
    btnLocate.addEventListener('click', () => {
        statusMessage.classList.add('hidden');
        
        if (!navigator.geolocation) {
            showError("Geolocation is not supported by your browser.");
            return;
        }

        btnLocate.innerHTML = '<span class="spinner" style="width:20px;height:20px;border-width:2px;margin:0;"></span> Locating...';
        btnLocate.disabled = true;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                fetchRecommendation(lat, lng);
            },
            (error) => {
                showError("Unable to retrieve your location. Please check permissions or try Demo.");
                resetButtons();
            }
        );
    });

    // Demo Mode (San Francisco)
    btnDemo.addEventListener('click', () => {
        fetchRecommendation(37.7749, -122.4194);
    });

    // Reset UI
    btnReset.addEventListener('click', () => {
        resultCard.classList.add('hidden');
        locationCard.classList.remove('hidden');
        resetButtons();
    });

    function showError(msg) {
        statusMessage.textContent = msg;
        statusMessage.className = 'status-message error';
    }

    function resetButtons() {
        btnLocate.innerHTML = '<span class="btn-icon">🧭</span> Auto-Locate Me';
        btnLocate.disabled = false;
    }

    async function fetchRecommendation(lat, lng) {
        // Transition UI
        locationCard.classList.add('hidden');
        loadingState.classList.remove('hidden');

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lat, lng })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            
            // Populate Data
            fatigueLevelEl.textContent = data.fatigue_level;
            fatigueLevelEl.className = `badge ${data.fatigue_level}`;
            fatigueReasonEl.textContent = data.fatigue_reason;
            recommendationTextEl.textContent = data.decision;

            // Show Results
            loadingState.classList.add('hidden');
            resultCard.classList.remove('hidden');
            
        } catch (error) {
            console.error(error);
            loadingState.classList.add('hidden');
            locationCard.classList.remove('hidden');
            showError("Failed to connect to NutriBrain. Please try again.");
            resetButtons();
        }
    }
});
