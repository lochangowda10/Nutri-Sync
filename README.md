# 🧠 NutriSync — AI-Powered Food Decision Engine

> *An AI-powered food decision engine that helps users make healthier choices before they eat — not after.*

Built for the **AMD Slingshot Hackathon 2026**.

## 🎯 Problem Statement
Helping individuals make better food choices by leveraging contextual inputs.

## 💡 What Makes NutriSync Different
NutriSync is NOT a calorie counter. It's a **preventive food decision system** that influences behavior *before* unhealthy eating happens, using context-aware AI recommendations, habit tracking, and behavioral analysis.

## 🚀 Core Features

### 1. 🧠 Food Decision Intelligence
When you log food, the AI asks *why* you're eating — stress, boredom, cravings, social pressure, or genuine hunger. It detects unhealthy patterns over time.

### 2. 🎯 Context-Aware Smart Recommendations
Uses time of day, sugar budget, protein balance, previous meals, and eating history to give intelligent advice. Example: *"It's 11:30 PM, you exceeded your sugar intake today — yogurt would be better than ice cream."*

### 3. 🔄 Smart Food Substitute Engine
Instead of restricting, it recommends realistic healthier alternatives. Example: Instead of *"Don't eat pizza"*, it suggests *"Choose thin crust or try a protein wrap."*

### 4. 🔥 7-Day Healthy Habit Engine
Streak-based habit tracking: No sugary drinks, breakfast consistency, water goals, reduced late-night snacking, and daily protein completion — with visual progress.

### 5. 🇮🇳 Indian Local Food Intelligence
Database of 75+ common Indian foods (idli, dosa, biryani, poha, samosa, chai, thali meals) with culturally relevant health recommendations.

### 6. 📊 Weekly AI Behavior Report
Detects patterns: breakfast skipping, sugar cravings after 9 PM, weekend overeating, low protein on weekdays, stress eating during work hours.

### 7. 📈 Measurable Impact Dashboard
Shows health improvement metrics: healthy decisions made, sugar reduction, consistency scores, and healthier replacement adoption.

## 🏗️ Tech Stack
- **Backend:** Python / FastAPI (strict typing with Pydantic)
- **Frontend:** Vanilla HTML/CSS/JS with Chart.js
- **Data:** localStorage (zero-setup for judges)
- **Deployment:** Google Cloud Run via Docker

## 🚀 Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Open `http://127.0.0.1:8000`

## ☁️ Deploy to Google Cloud Run
```bash
gcloud run deploy nutrisync --source . --region asia-south1 --allow-unauthenticated --port 8080
```

## 🔒 Security
API keys managed via environment variables and Google Secret Manager. No credentials stored in source code.

---
*Built for AMD Slingshot 2026. Making healthier food decisions, one AI insight at a time.*
