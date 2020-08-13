# PDF zu Fließtext mit Maschinellem Lernen

> Durch lange Wörter in der Deutschen Sprache ist Text in PDF bei Zeilenumbrüchen zerstückelt.
> `pd3f` rekonsturiert mithilfe von Maschinellem Lernen den ursprünglichen Fließtext.

PDFs sind für Menschen gemacht und nicht für Maschinen.
Das führt dazu, dass wir sie lesen können, aber Maschinen Probleme haben Text zu extrahieren.
Das ist jedoch notwendig, um z. B. über große Mengen von PDFs im Rahmen journalistischer Recherchen auszuwerten.
Oder Personen mit Seheinschränkungen sind darauf angewiesen, dass Computer ihnen Texte vorlesen.
Und auch im Rahmen der bereits erfolgen oder geplanten Digitaliserung Deutscher Behörden müssen großen Aktenbestände digitalisert werden.

## `pd3f`

Im Rahmen der Protoype-Förderung von “DDD: Deutsche Dokumente Digitalisieren” ist die Software-Lösung `pd3f` entstanden, um `guten` Text aus PDF zu rekonstruieren.
Gut in dem Sinne, dass der ursprüngliche Text – ohne unnötige Zeilenumbrüche – wiederhergestellt werden kann.
Aus dem zerstückelten Text im PDF wird somit ein digitaler Fließtext.
Gerade im Deutschen gibt es auf Grund der Besonderheiten mit langen (zusammengesetzen) Wörtern den Fall, dass Wörter am Zeilenende getrennt werden.
Bei einer üblichen Text-Extraktion werden durchgetrennte Wörter nicht wiederzusammengefügt.
Damit kann das ursprüngliche Wort z. B. nicht mehr per Suche gefunden werden.
Und weiterführenden Anwendung, wie z. B. die automatisierte Erkennung von Eigennamen (Named-Entity Recognition) wird erschwert.

## Automatsierte Texterkennung

Text auf gescannten Dokumenten zu erkennen (OCR) erfolgt schon heute zufriedenstellend mit Open-Source-Lösungen.
Aber es ist aber weiterhin ein Problem die Wörter aus einem PDF zu Text zusammenfassen.
Das hängt mit dem veralteten Portable Document Format (PDF) zu tun.
Das Format folgt der Idee des Druckens und in ihm wird Fließtext nicht als Text dargestellt.
So wird teilweise jedem einzelnen Buchstaben als Zeichen kodiert und eine Position (x- und y-Wert für Höhe und Breite) auf dem (virtuellen) Blatt Papier zugewiesen.

Um aus diesem Buchstaben-Salat nutzen bestehen Tools Heuristiken, um Buchstaben zu Wörter zuzusammen zu setzen.
Aus Wörter müssen wieder Zeilen werden und anschließend müssen die Zeilen zu Paragraphen zusammenzufassen.
Das ist eine ohnehin schwierige Aufgabe.
Das Open-Source-Tool [Parsr](https://github.com/axa-group/Parsr) von dem französischen Versicherungskonzern Axa sorg immerhin hier schon für Besserung.
Es zerlegt relativ erfolgreich ein PDF in seine Zeilen und Paragrafen.
Das Tool ist erst einige wenige Monate vor dem Start der Projektförderung erschienen und erwieß sich als nützlich.
Unsere Software `pd3f` nutzt die Ausgabe von Parsr, um darauf aufbauen guten Text wiederherzustellen.

Eigentlich eine einfache Aufgabe: Alle Wörter mit einem "–" am Zeilende werden mit dem Wort auf der darauffolgenden Zeile zusammengefügt wie in diesem Beispiel.

> ... die Bedeutung der finan-
>
> ziellen Interessen der Union ...

Das Wort "finanziellen" entspricht dem ursprünglichen Text.

Es gibt aber auch "-" am Zeilenden, das nicht entfernt werden darf, weil es Bestandteil des Worter ist.
Anbei ein Beispiel.

> Auch andere EU-
>
> Staaten, wie bspw. Polen, ...

"EUStaaten" wären nicht korrekt.
Um da weiterzukommen, braucht es mehr Verständnis über die deutsche Sprache.
Hier kommt Maschinelles Lernen in Form von Sprachmodellen zum Einsatz.

## Was sind Sprachmodelle? (Language Models)

Bei Sprachmodelle geht es darum, dass ein Computer-Programm zukünftige Wörter auf der Basis von vergangen Wörter lernt.
Zum Einsatz kommen Sprachmodelle z. B. auf Smartphones bei der Autovervollständigung.
Sprachmodelle verinnerlichen die Characteristiken der Deutschen Sprachen und können vorhersagen, welche Wörter oder Buchstaben wahrscheinlich als nächsten Kommen.
So kommt nach den beiden Wörtern "Sehr geehrte" wahrscheinlich das Wort "Frau" als nächstes.

Solche Sprachmodelle operieren auf ganzen Wörtern oder auch nur auf Buchstaben.

## `dehyphen`

Eine Unterkomponente von `pd3f` ist das Software-Packet `dehyphen`, welches ebenfalls im Rahmen der Förderung entstand.
Es benutzt Sprachmodelle, um zu entschieden ob ein "-" am Zeilenende entfernt werden sollte oder nicht.
Die Grundidee: Es wird berechntet, welche die wahrscheinliche Weg ist zwei Zeilen zu verbinden.

> Auch andere EU-
>
> Staaten, wie bspw. Polen, ...

Bei dem obrigen Beispiel spuckt `dehyphen` das richtige Ergebnisse aus: "EU-Staaten" und nicht "EUStaaten".
`dehyphen` ist ein Modul, welches von anderen Software-Entwickler:innen einfach wiederverwendet werden kann.

## Datenverarbeitungs-Pipeline `pd3f`

Das Hauptergebnis der Förderung ist `pd3f`: Eine komplette Anwendung und eine Datenverarbeitungs-Pipeline für PDFs.
Diese kann betrieben werden, um (Deutsche) Dokumente zu digitalisieren.
Auf einem gescannten Dokument wird der Text automatsiert gescannt, dass wird mithilfe von Parsr der Text in Wörter, Linies und Paragraphenn unterteilt.
Anschließend wird mithilfe von `dehyphen`
Anbei eine schematische Auflistung.

![flow.jpg]()

Der Fokus liegt auf dem Deutschen mit seinem langen Wörtern, es kann aber auch für andere Sprachen angewandt werden.
`pd3f` ist aktuell auch für Englisch, Spanisch und Französisch verfügbar.

[Zur Demo von `pd3f`](https://demo.pd3f.com)

## Weitere Arbeit

Da Dokumente in so vielen unterschiedlichen Formen vorkommt, funktioniert `pd3f` nicht für alle.
Gerade bei schlecht gescannten PDFs ist der Text nicht so gut.
Was jetzt noch fehlt ist eine systematische Veröffentlichung der Resultate von `p3d`.
Diese wird vorraussichtlich im September 2020 erfolgen.
Der Code wird online <https://github.com/pd3f> stehen und weiter gepflegt.
Ich danke dem BMBF für die Förderung des Projekts.