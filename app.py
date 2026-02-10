from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pickle
import os

# -----------------------------
# Load preprocessed DataFrame
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "nutrition_df.pkl"), "rb") as f:
    df = pickle.load(f)

# -----------------------------
# App setup
# -----------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------
# BMI helpers
# -----------------------------
def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


daily_calorie_target = {
    "Underweight": "2800–3000 kcal/day",
    "Normal": "2000–2200 kcal/day",
    "Overweight": "1600–1800 kcal/day",
    "Obese": "1200–1500 kcal/day"
}

bmi_cluster_pref = {
    "Underweight": ["Energy Dense", "High Carb"],
    "Normal": ["High Protein", "High Carb"],
    "Overweight": ["Low Calorie", "High Protein"],
    "Obese": ["Low Calorie"]
}

dietary_options = ["Vegan", "Vegetarian", "Omnivore", "Pescatarian"]

# -----------------------------
# Meal recommendation
# -----------------------------
def recommend_meals(bmi_cat, dietary_pref=None):
    preferred_clusters = bmi_cluster_pref.get(bmi_cat, [])
    recommendations = df[df["Cluster_Type"].isin(preferred_clusters)]

    if dietary_pref:
        recommendations = recommendations[
            recommendations["Dietary Preference"]
            .fillna("")
            .str.contains(dietary_pref, case=False)
        ]

    def get_list(col):
        return recommendations[col].dropna().unique().tolist()

    meals = {
        "Breakfast": get_list("Breakfast Suggestion"),
        "Lunch": get_list("Lunch Suggestion"),
        "Dinner": get_list("Dinner Suggestion"),
        "Snacks": get_list("Snack Suggestion"),
    }

    if not any(meals.values()):
        meals = {
            "Breakfast": df["Breakfast Suggestion"].dropna().unique().tolist(),
            "Lunch": df["Lunch Suggestion"].dropna().unique().tolist(),
            "Dinner": df["Dinner Suggestion"].dropna().unique().tolist(),
            "Snacks": df["Snack Suggestion"].dropna().unique().tolist(),
        }

    return meals

# -----------------------------
# HTML template
# -----------------------------
form_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Meal Recommendation</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body {
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
    min-height: 100vh;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.card {
    background: #fff;
    max-width: 520px;
    width: 100%;
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.12);
}

h2 {
    text-align: center;
    margin-bottom: 24px;
    color: #2d3748;
}

label {
    font-weight: 600;
    color: #4a5568;
    display: block;
    margin-bottom: 6px;
}

input, select {
    width: 100%;
    padding: 12px;
    margin-bottom: 16px;
    border-radius: 8px;
    border: 1px solid #cbd5e0;
}

button {
    width: 100%;
    background: #667eea;
    color: #fff;
    border: none;
    padding: 14px;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
}

button:hover {
    background: #5a67d8;
}

.results {
    margin-top: 28px;
    border-top: 1px solid #e2e8f0;
    padding-top: 20px;
    animation: fadeUp 0.6s ease-out forwards;
}

.badge {
    background: #edf2f7;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    margin-left: 6px;
}

.meal {
    opacity: 0;
    margin-top: 14px;
    animation: fadeUp 0.6s ease-out forwards;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

ul { padding-left: 18px; }

li {
    color: #4a5568;
    margin-bottom: 6px;
}
</style>
</head>

<body>
<div class="card">
    <h2>🥗 Meal Recommendation</h2>

    <form method="post">
        <label>Height (cm)</label>
        <input type="number" name="height" step="0.1" required>

        <label>Weight (kg)</label>
        <input type="number" name="weight" step="0.1" required>

        <label>Dietary Preference</label>
        <select name="dietary_preference">
            <option value="">No preference</option>
            {% for option in dietary_options %}
            <option value="{{ option }}">{{ option }}</option>
            {% endfor %}
        </select>

        <button type="submit">Get Recommendations</button>
    </form>

    {% if result %}
    <div class="results">
        <p><strong>BMI:</strong> {{ result.BMI }}</p>
        <p>
            <strong>Category:</strong> {{ result.BMI_Category }}
            <span class="badge">{{ result.Daily_Calorie_Target }}</span>
        </p>

        {% for meal, items in result.Recommended_Meals.items() %}
        <div class="meal">
            <strong>{{ meal }}</strong>
            <ul>
                {% for item in items[:5] %}
                <li>{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}

        <!-- Notes Section -->
        <div class="meal">
            <strong>📝 Notes</strong>
            <ul>
                <li><strong>Eat good, feel good, live good.</strong></li>
                <li>
                    Having nutritious food at the right time is crucial for optimizing metabolism,
                    sustaining energy, and supporting long-term health.
                </li>
                <li><strong>Meal Timing Guidelines:</strong></li>
                <li>🍳 Breakfast: <strong>Before 9 AM</strong></li>
                <li>🍛 Lunch: <strong>1 – 2 PM</strong></li>
                <li>🥜 Snacks: <strong>3 – 4 PM</strong></li>
                <li>🍽️ Dinner: <strong>Before 7 – 8 PM</strong></li>
            </ul>
        </div>

    </div>
    {% endif %}
</div>
</body>
</html>
"""

# -----------------------------
# Route
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def recommend():
    result = None

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        try:
            height = float(data.get("height"))
            weight = float(data.get("weight"))
            dietary_pref = data.get("dietary_preference") or None
        except Exception:
            return jsonify({"error": "Invalid input"}), 400

        bmi = weight / ((height / 100) ** 2)
        bmi_cat = bmi_category(bmi)

        result = {
            "BMI": round(bmi, 2),
            "BMI_Category": bmi_cat,
            "Daily_Calorie_Target": daily_calorie_target[bmi_cat],
            "Recommended_Meals": recommend_meals(bmi_cat, dietary_pref),
        }

        if request.is_json:
            return jsonify(result)

    return render_template_string(form_html, result=result, dietary_options=dietary_options)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
