report_template = """<!doctype html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport"
        content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>Schulsprecherwahl Bericht</title>
  <style>
    body {
      background-color: #eeeeee;
      font-family: sans-serif;
    }

    .container {
      background-color: white;
      margin: 15px auto;
      padding: 8px 25px;
      width: 800px;
      box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.3);
    }

    h1 {
      text-align: center;
    }

    h3 {
      margin: 12px 0 10px;
      text-align: right;
    }

    .participant {
      margin-bottom: 20px;
      padding: 5px 3px 5px 10px;
      border-left: 3px solid lightblue;
    }

    .participant:hover {
      background-color: #f6f6f6;
      border-radius: 3px;
    }

    .participant > h4 {
      margin: 0;
      color: orange;
    }

    .participant > h4 > small {
      color: black;
    }

    .participant > p {
      color: #808080;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Schulsprecherwahl {{ today.year }} Bericht</h1>
    <p>Die genauen Ergebnisse der Schulsprecherwahl am {{ today.strftime("%d.%m.%Y") }}.</p>
    <p>{{ valid_votes }} gültige Stimmen und<br>
      {{ invalid_votes }} ungültige Stimmen.
    </p>
    <p>Insgesamt wurden {{ sum_points }} Punkte bei der Wahl vergeben.</p>

    <h3>Ergebnisse
      <small>({{ participants|length }} Teilnehmer)</small>
    </h3>
    {% for partic in participants %}
      <div class="participant">
        <h4>
          <small>#{{ loop.index }}</small>
          {{ partic.name }}
        </h4>
        <p>{{ partic.points }} Punkte ({{ "{:.2f}".format(partic.points_perc) }}% der Gesamtpunkte)</p>
        <ul>
          {% for top_vote, num_votes in partic.top_votes.items() %}
            <li>Anzahl an {{ top_vote }}. Stimmen: {{ num_votes }}</li>
          {% endfor %}
        </ul>
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""