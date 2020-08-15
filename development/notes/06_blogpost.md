---
layout: project (tragen wir ein)
title:  `pd3f: PDF zu Fließtext mit Maschinellem Lernen
image: /path/to/Beitragfsfoto-DDD_1500.jpg
video: (tragen wir ein)
tags: (tragen wir ein)
authors: Johannes Filter
summary: Durch lange Wörter im Deutschen sind aus PDF extrahierte Texte mit Zeilenumbrüchen zerstückelt. `pd3f` rekonsturiert mithilfe von Maschinellem Lernen den ursprünglichen Fließtext.
---


# PDF zu Fließtext mit Maschinellem Lernen

> Durch lange Wörter im Deutschen sind aus PDF extrahierte Texte mit Zeilenumbrüchen zerstückelt.
> `pd3f` rekonsturiert mithilfe von Maschinellem Lernen den ursprünglichen Fließtext.

PDFs sind für Menschen gemacht und nicht für Maschinen.
Das führt dazu, dass wir sie lesen können, aber Maschinen Probleme haben Text zu extrahieren.
Das ist jedoch notwendig, um z. B. über große Mengen von PDFs im Rahmen journalistischer Recherchen auszuwerten.
Oder Personen mit Seheinschränkungen sind darauf angewiesen, dass Computer ihnen Texte vorlesen.
Und auch im Rahmen der bereits erfolgten oder geplanten Digitalisierung deutscher Behörden müssen großen Aktenbestände digitalisert werden.

## Text extrahieren mit `pd3f`

Im Rahmen der Protoype-Förderung von "DDD: Deutsche Dokumente Digitalisieren" ist die Software-Lösung `pd3f` entstanden, um "guten" Text aus PDF zu rekonstruieren.
Gut in dem Sinne, dass der ursprüngliche Text – ohne unnötige Zeilenumbrüche – wiederhergestellt werden kann.
Aus dem zerstückelten Text im PDF wird somit wieder ein digitaler Fließtext.
Gerade im Deutschen mit seiner langen Wörtern gibt es die Besonderheit, dass Wörter am Zeilenende getrennt werden.
Bei einer üblichen Text-Extraktion werden durchgetrennte Wörter nicht wiederzusammengefügt.
Damit kann das ursprüngliche Wort z. B. nicht mehr per Suche gefunden werden.
Und weiterführenden Anwendungen, wie z. B. die automatisierte Erkennung von Eigennamen (Named-Entity Recognition) wird erschwert.

## Automatisierte Texterkennung

Texterkennung auf gescannten Dokumenten (Optical Character Recognition / OCR) erfolgt schon heute zufriedenstellend mit Open-Source-Lösungen.
Aber es ist aber weiterhin ein Problem die Wörter aus einem PDF zu Text zusammenfassen.
Das hängt mit dem veralteten Portable Document Format (PDF) zu tun.
Das Format folgt der Idee des Druckens und in ihm wird Fließtext nicht als Text dargestellt.
So wird teilweise jedem einzelnen Buchstaben als Zeichen kodiert und eine Position (x- und y-Wert für Höhe und Breite) auf dem (virtuellen) Blatt Papier zugewiesen.

![pdf_buchstaben.jpg]()

Um aus diesem Buchstaben-Salat nutzen bestehen Tools Heuristiken, um Buchstaben zu Wörter zuzusammen zu setzen.
Aus Wörter müssen wieder Zeilen werden und anschließend müssen die Zeilen zu Paragraphen zusammengefasst werden.
Das ist eine ohnehin schwierige Aufgabe, da es nahezu endlose Möglichkeiten gibt, wie Text aussehen.
Das Open-Source-Tool [Parsr](https://github.com/axa-group/Parsr) von dem französischen Versicherungskonzern Axa sorgt immerhin hier schon für Besserung.
Es zerlegt relativ erfolgreich ein PDF in seine Zeilen und Paragrafen.
Das Tool ist erst einige wenige Monate vor dem Start der Projektförderung erschienen und erwieß sich als nützlich.
Unsere Software `pd3f` füttert zunächste das PDF in Parsr und nutzt die Ausgabe von Parsr, um darauf aufbauend guten Text wiederherzustellen.

## Zeilenumbrüche entfernen

Worttrennung an Zeilenumbrüchen zu entfernen, ist eigentlich eine einfache Aufgabe: Alle Wörter mit einem "–" am Zeilende werden mit dem Wort auf der darauffolgenden Zeile zusammengefügt wie in diesem Beispiel.

> ... die Bedeutung der finan-
>
> ziellen Interessen der Union ...

Das Wort "finanziellen" entspricht dem ursprünglichen Text.

Es gibt aber auch "-" am Zeilenden, das nicht entfernt werden darf, weil es Bestandteil des Worter ist.
Anbei ein Beispiel.

> Auch andere EU-
>
> Staaten, wie bspw. Polen, ...

Um da weiterzukommen, braucht es mehr Verständnis über die deutsche Sprache.
Hier kommt Maschinelles Lernen in Form von Sprachmodellen zum Einsatz.

## Was sind Sprachmodelle? (Language Models)

Bei Sprachmodelle geht es darum, dass ein Computer-Programm zukünftige Wörter auf der Basis von vergangennen Wörter lernt.
Zum Einsatz kommen Sprachmodelle z. B. auf Smartphones bei der Autovervollständigung.
Sprachmodelle verinnerlichen die Charakteristiken der Deutschen Sprachen und können vorhersagen, welche Wörter oder Buchstaben wahrscheinlich als nächsten kommen.
So kommt nach den beiden Wörtern "Sehr geehrte" wahrscheinlich das Wort "Frau" als nächstes.

Solche Sprachmodelle operieren auf ganzen Wörtern oder auch nur auf Buchstaben (um folgende Buchstaben zu erraten).

## Texte reparieren mit `dehyphen`

Eine Unterkomponente von `pd3f` ist das Software-Packet `dehyphen`, welches ebenfalls im Rahmen der Förderung entstand.
Es benutzt Sprachmodelle, um zu entschieden ob ein "-" am Zeilenende entfernt werden sollte oder nicht.
Die Grundidee: Es wird berechntet, welche die wahrscheinliche Möglichkeit ist, zwei Zeilen zu verbinden.

> Auch andere EU-
>
> Staaten, wie bspw. Polen, ...

Bei dem obrigen Beispiel spuckt `dehyphen` das richtige Ergebnisse aus: "EU-Staaten" und nicht "EUStaaten".
`dehyphen` ist ein Modul, welches von anderen Software-Entwickler:innen einfach wiederverwendet werden kann.

## Datenverarbeitungs-Pipeline `pd3f`

Das Hauptergebnis der Förderung ist `pd3f`: Eine komplette Anwendung und eine Datenverarbeitungs-Pipeline für PDFs.
Diese kann betrieben werden, um (deutsche) Dokumente zu digitalisieren.
Auf einem gescannten Dokument wird der Text automatisiert gescannt, dann wird mithilfe von Parsr der Text in Wörter, Zeilen und Paragraphen unterteilt.
Anschließend wird mithilfe von `dehyphen` guter Text extrahiert.
Anbei eine schematische Auflistung der benutzten Komponennten.

![flow.jpg]()

[Zur Demo von `pd3f`](https://demo.pd3f.com)

Der Fokus liegt auf dem Deutschen mit seinem langen Wörtern, es kann aber auch für andere Sprachen angewandt werden.
`pd3f` ist aktuell auch für Englisch, Spanisch und Französisch verfügbar.

Das war nur einen kleinen Erklärung über die Möglichkeiten von `pd3f`.
Eine ausführlichere Dokumentation liegt dem Quellcode bei.
Der Code wird online <https://github.com/pd3f/pd3f> stehen und weiter gepflegt.
Die Hauptfunktionalitäten von `pd3f` sind noch mal in einem eigenen Python-Packet <https://github.com/pd3f/pd3f-core> gebündelt, sodass auch hier eine einfache Weiterverwendung möglich ist.

## Weitere Arbeit

Da Dokumente in so vielen unterschiedlichen Formen vorkommt, funktioniert `pd3f` noch nicht für alle PDFs.
Gerade bei schlecht gescannten PDFs ist der extrahierte Text noch stark verbesserungsbedürftig.
Es ist unwahrscheinlich, dass `pd3f` jemals für alle PDFs funktionieren wird.
Es wird aber weiterhin gearbeitet um das Resultate für z. B. mehr-spaltige Dokumente zu verbessern.

Was jetzt noch fehlt, ist eine systematische Evaluation der Text-Extrakte von `pd3f`.
Diese wird vorraussichtlich im September 2020 erfolgen.

Ich danke dem dem Prototypefund und dem DLR-Projektträger für die Betreuung des Projekts, Ame Elliott und Eileen Wagner von [Simply Secure](https://simplysecure.org/) für das Coaching und dem BMBF für die finanzielle Förderung.

Website: <https://pd3f.com>
Twitter: <https://twitter.com/pd3f_>
GitHub: <https://github.com/pd3f>

von Johannes Filter

Webseite: <https://johannesfilter.com>
Twitter: <https://twitter.com/fil_ter>
