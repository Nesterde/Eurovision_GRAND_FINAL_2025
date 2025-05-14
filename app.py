from flask import Flask, render_template, request, redirect, url_for
import json
import os
from artists import artists

app = Flask(__name__)
VOTE_FILE = "votes.json"
POINTS = [12, 10, 8, 7, 6, 5, 4, 3, 2, 1]

# Tworzenie pliku z głosami jeśli nie istnieje
if not os.path.exists(VOTE_FILE):
    with open(VOTE_FILE, "w") as f:
        json.dump([], f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        gender = request.form.get("gender")
        city = request.form.get("city")
        rankings = request.form.getlist("artist")

        if len(rankings) != 10 or len(set(rankings)) != 10:
            return "Musisz wybrać dokładnie 10 różnych artystów!"

        with open(VOTE_FILE, "r") as f:
            votes = json.load(f)

        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

        if any(v.get('ip') == user_ip for v in votes):
           return render_template("error.html", message="Z tego adresu IP już oddano głos. Można głosować tylko raz.")

        if any(v['name'].strip().lower() == name.strip().lower() for v in votes):
           return render_template("error.html", message="To imię już oddało głos. Można głosować tylko raz.")


        vote = {
            "name": name,
            "gender": gender,
            "city": city,
            "votes": dict(zip(rankings, POINTS)),
            "ip": user_ip
        }

        votes.append(vote)

        with open(VOTE_FILE, "w") as f:
            json.dump(votes, f, indent=2)

        return redirect(url_for("results"))

    return render_template("index.html", artists=artists)

def get_results_by_category(votes, category_key):
    category_scores = {}
    for vote in votes:
        category_value = vote.get(category_key)
        if not category_value:
            continue
        if category_value not in category_scores:
            category_scores[category_value] = {}
        for artist, points in vote["votes"].items():
            category_scores[category_value][artist] = category_scores[category_value].get(artist, 0) + points

    # Filtrowanie artystów z >0 punktów i sortowanie
    sorted_results = {
        category: sorted(
            [(artist, pts) for artist, pts in scores.items() if pts > 0],
            key=lambda x: x[1],
            reverse=True
        )
        for category, scores in category_scores.items()
    }
    return sorted_results

@app.route("/results")
def results():
    with open(VOTE_FILE, "r") as f:
        votes = json.load(f)

    # Obliczanie ogólnych wyników
    scores = {artist: 0 for artist in artists}
    for vote in votes:
        for artist, pts in vote["votes"].items():
            scores[artist] += pts

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Wyniki wg płci i miasta (już posortowane wewnątrz funkcji)
    results_by_gender = get_results_by_category(votes, "gender")
    results_by_city = get_results_by_category(votes, "city")

    return render_template(
        "results.html",
        ranked=ranked,
        all_votes=votes,
        results_by_gender=results_by_gender,
        results_by_city=results_by_city,
    )

if __name__ == "__main__":
    app.run(debug=True)