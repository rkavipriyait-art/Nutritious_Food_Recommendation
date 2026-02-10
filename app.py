from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pickle
import os

# Load preprocessed DataFrame
with open("nutrition_df.pkl", "rb") as f:
    df = pickle.load(f)

app = Flask(__name__)
# app = Flask(__name__)
# CORS(app)


# BMI functions
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


# Meal recommendation function
def recommend_meals(bmi_cat, dietary_pref=None):
    preferred_clusters = bmi_cluster_pref.get(bmi_cat, [])
    recommendations = df[df["Cluster_Type"].isin(preferred_clusters)]

    if dietary_pref:
        recommendations = recommendations[
            recommendations["Dietary Preference"].fillna("").str.contains(dietary_pref, case=False)
        ]

    breakfast = recommendations["Breakfast Suggestion"].dropna().unique().tolist()
    lunch = recommendations["Lunch Suggestion"].dropna().unique().tolist()
    dinner = recommendations["Dinner Suggestion"].dropna().unique().tolist()
    snacks = recommendations["Snack Suggestion"].dropna().unique().tolist()

    # Fallback if no meals found
    if not (breakfast or lunch or dinner or snacks):
        breakfast = df["Breakfast Suggestion"].dropna().unique().tolist()
        lunch = df["Lunch Suggestion"].dropna().unique().tolist()
        dinner = df["Dinner Suggestion"].dropna().unique().tolist()
        snacks = df["Snack Suggestion"].dropna().unique().tolist()

    return {
        "Breakfast": breakfast,
        "Lunch": lunch,
        "Dinner": dinner,
        "Snacks": snacks
    }


# HTML template
form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Meal Recommendation</title>
</head>
<body>
    <h2>Enter Your Details</h2>
    <form method="post" action="/">
        Height (cm): <input type="text" name="height" required><br><br>
        Weight (kg): <input type="text" name="weight" required><br><br>
        Dietary Preference:
        <select name="dietary_preference">
            {% for option in dietary_options %}
                <option value="{{ option if option != 'None' else '' }}"
                    {% if result and result.dietary_pref == option %} selected {% endif %}>
                    {{ option }}
                </option>
            {% endfor %}
        </select><br><br>
        <input type="submit" value="Get Recommendations">
    </form>

    {% if result %}
    <hr>
    <h3>Results:</h3>
    <p><b>BMI:</b> {{ result.BMI }}</p>
    <p><b>BMI Category:</b> {{ result.BMI_Category }}</p>
    <p><b>Daily Calorie Target:</b> {{ result.Daily_Calorie_Target }}</p>
    <h4>Recommended Meals:</h4>
    <ul>
        {% for meal, items in result.Recommended_Meals.items() %}
        <li><b>{{ meal }}:</b> {{ items | join(', ') if items else 'No suggestions' }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""


# Single endpoint for both HTML and JSON
@app.route("/", methods=["GET", "POST"])
def recommend():
    result = None

    if request.method == "POST":
        # Check if JSON or form submission
        if request.is_json:
            data = request.get_json()
            height = float(data.get("height"))
            weight = float(data.get("weight"))
            dietary_pref = data.get("dietary_preference", None)
            if dietary_pref == "":
                dietary_pref = None
        else:
            # Form submission
            height = float(request.form.get("height"))
            weight = float(request.form.get("weight"))
            dietary_pref = request.form.get("dietary_preference", None)
            if dietary_pref == "":
                dietary_pref = None

        # Calculate BMI
        bmi = weight / ((height / 100) ** 2)
        bmi_cat = bmi_category(bmi)
        calorie_target = daily_calorie_target[bmi_cat]
        meals = recommend_meals(bmi_cat, dietary_pref)

        result = {
            "BMI": round(bmi, 2),
            "BMI_Category": bmi_cat,
            "Daily_Calorie_Target": calorie_target,
            "Recommended_Meals": meals,
            "dietary_pref": dietary_pref or "None"
        }

        # If JSON request, return JSON
        if request.is_json:
            return jsonify(result)

    # For GET request or form submission, render HTML
    return render_template_string(form_html, result=result, dietary_options=dietary_options)


# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)