# Dokumente zu Text mit DDD

PDFs sind für Menschen gemacht und nicht für Maschinen.
Das führt dazu, dass wir sie lesen können, aber Maschinen Probleme haben Text zu extrahieren.
Das ist jedoch notwendig, um z. B. über große Mengen von PDFs im Rahmen journalistischer Recherchen auszuwerten.
Oder auch Menschen mit Seheinschränkungen sind darauf angewiesen, dass Computer ihnen Text vorlesen.

Im Rahmen der Förderung von “DDD: Deutsche Dokumente Digitalisieren” sind mehrere Software-Lösung entstanden, um `guten` Text aus PDF zu rekonstruieren.
Gut in dem Sinne, dass der ursprüngliche Text – ohne unnötige Zeilenumbrüche – wiederhergestellt werden kann.
Gerade im Deutschen gibt’s auf Grund der Besonderheiten mit langen (zusammengesetzen) Wörtern den Fall, dass Wörter getrennt werden.
So kommt es dazu, dass Wörter aufgeteilt werden.
Bei einer üblichen Text-Extraktion werden so durchgetrennte Wörter genommen.

## Texterkennung

Text auf gescannten Dokumenten zu erkennen (OCR) erfolgt schon heute zufriedenstellend mit Open-Source-Lösungen.
Aber es ist aber weiterhin ein Problem die Wörter aus einem PDF zu Text zusammenfassen.
Das hängt mit dem veralteten Portable Document Format (PDF) zu tun.
In diesem wird Fließtext nicht als Text dargestellt.
Es kam aus der Idee des Druckens.
So wird teilweise jedem einzelnen Buchstaben eine Position (x- und y-Wert für Höhe und Breite) auf dem (virtuellen) Blatt Papier zugewiesen.

Um jetzt aus disem Buchstaben-Salat nutzen bestehen Tools Heuristiken, um Buchstaben zu Wörter zuzusammen zu setzen.
Aus Wörter müssen wieder Zeilen werden und anschließend müssen die Zeilen zu Paragraphen zusammenzufassen.
Das ist eine ohnehin schwierige Aufgabe.
Das Open-Source-Tool `parsr` von dem französischen Versicherungskonzern Axa sorg immerhin hier schon für Besserung.
Es zerlegt relativ erfolgreich ein PDF in seine Zeilen und Paragrafen.
Das Tool ist erst einige wenige Monate vor start von DDD erschienen und erwieß sich als nützlich.
Doch Ziel von DDD ist es, guten Text zu extrahieren.
Denn auch der Text-Output von parsr sorg dafür, dass

Eigentlich eine Einfache Aufgabe: Alle Wörter mit – am Ende werden mit dem Wort auf der Darauffolgenden Zeile zusammengefügt, hier ein Beispiel.

> die Bedeutung der finan-
>
> ziellen Interessen der Union

Ja, aber dann gibt es Beispiele wie hier:

> Auch andere EU-
>
> Staaten, wie bspw. Polen,

"EUStaaten" wären nicht korrekt.
Um da weiterzukommen, braucht es mehr Verständnis über die deutsche Sprache.
Hier kommt Sprachmodelle zum Einsatz.

## Exkurs Sprachmodelle (Language Models)

Bei Sprachmodelle geht es darum, dass das Modell zukünftige Wörter auf der Basis von vergangen Wörter lernt.
Das passiert auf großen Textmengen, die gerade frei zu verfügung stehen.
Dann wird das Modell trainiert um zukünftige Wörter zu lernen.
Ein Einsatz finden das auf Smart phones und der Autovervollständigung.
Es gibt es auf Wörtern oder Buchstaben.
Wir ben

## pdddf

Ein Tool das im Rahmen von DDD gefördert wurde ist `pdddf`.
Es benutzt Sprachmodelle, um zu entschieden ob "-" entfernt werden oder nicht.
Die Grundidee: Zunächst werden Kandidaten gefunden, wie zwei Zeilen verbunden werden könnten.
Mit –, ohne – und space weg und mit normalen Space.
Das am wahrscheinlichsten ist, wird genommen.

(Konkret wird perplexity mit Flair berechnet)

Bei dem obiegen Beispiel spuckt `pdddf` das richtige Ergebnisse aus.
`pdddf` ist ein Modul, welches von anderen Software-Entwickler:innen einfach wiederverwendet werden kann.

## pd3f

Im Rahmen von DDD ist nicht nur das Packet entscheiden, sondern auch eine komplette Anwendung, eine Datenverarbeitungs Pipeline.
Diese kann betrieben werden, um (Deutsche) Dokumente zu digitalisieren.
Eine große Anzahl von Software wird genutzt.
Anbei eine schematische Auflistung.

[TODO]

Der Fokus liegt auf dem Deutschen mit seinem langen Wörtern, es kann aber auch für andere Sprachen angewandt werden.
In `pd3f` sind aktuell auch Englisch, Spanisch und Französisch verfügbar.

[Zur Demo von `pd3f`](demo.pd3f.com)

Es gibt aber noch viel zu tun: Viele PDFs sehen unterschiedliche aus. Gerade bei schlecht gescannten PDFs ist der Text nicht so gut. Vieles ist noch möglich.
Was jetzt noch fehlt ist eine systematische Veröffentlichung. Diese wird vorraussichtlich im Septerm 2020 erscheiben.