# eventfeed Generator for Domjudge 7.1.1

While eventfeed not recoreding the contest fully correct, the `event` sheet become not trustable.

But scoreboard stile avaliable, so I try to recalculate one from other sheets.

## files

* genevent.py

  connect to Domjudge database and try to recalculate `eventfeed.json`.

  requirement: pypyodbc + mysql odbc driver (rewrite with other lib soon), webcolors (option)

* jsonl2json.py

  load old `eventfeed.json` (from domjudge >= 7.0) and gen `feed.json` for [sortable](https://github.com/906030538/sortable)

* xml2json.py

  load old `eventfeed.xml` (from domjudge < 7.1 / PC^2) and gen `feed.json` for [sortable](https://github.com/906030538/sortable)

