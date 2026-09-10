# Quellen- und Webrecherche-Audit

**Fall:** `de/strafrecht/materielles-strafrecht/fortgeschrittenenklausur-die-reise-ins-gericht-wenn-der-einbruch-nach-hinten-losgeht`

## Zählung

- Suchanfragen: **37**
- Als verwendet belegte URLs: **8**
- Explizit als Open/Fetch protokollierte URLs: **0**
- In der Lösung zitierte URLs: **0**
- Eindeutige verwendete Quellen-URLs: **8**
- Eindeutige verwendete Domains: **4**
- Alle im Audit beobachteten URLs: **8**
- Verstöße gegen die Domain-Sperre: **0**
- Informativ markierte Suchanfragen: **41**

## Domain-Sperre

- Gesperrte Domains: `zjs-online.com`
- Status: **bestanden**
- Such-Leakage-Audit: **nur Hinweis; keine Verwerfung**

## Quellen

| Quelle | Domain | verwendet | Open/Fetch protokolliert | in Lösung zitiert | Zweck/Nachweis |
|---|---|:---:|:---:|:---:|---|
| [Link](https://juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py?Art=en&Blank=1.pdf&Datum=2020-1-22&Gericht=bgh&anz=18&nr=105630&pos=10) | `juris.bundesgerichtshof.de` | ja | nein | nein | Wohnungseigenschaft eines weiterhin funktionsfähigen Hauses nach dem Tod seiner einzigen Bewohner. |
| [Link](https://juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py?Art=en&Blank=1.pdf&Datum=2021-5-19&Gericht=bgh&anz=20&nr=118783&pos=15) | `juris.bundesgerichtshof.de` | ja | nein | nein | Bestätigung der Maßstäbe zum Versuchsbeginn beim Wohnungseinbruchdiebstahl. |
| [Link](https://juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py?Art=en&Blank=1.pdf&Datum=2022-10-25&Gericht=bgh&anz=31&client=13&nr=132514&pos=4) | `juris.bundesgerichtshof.de` | ja | nein | nein | Abgrenzung von Wohnung und dauerhaft genutzter Privatwohnung nach dem Tod des Bewohners sowie Tateinheit von vollendetem Grunddelikt und versuchter Qualifikation. |
| [Link](https://juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py?Art=en&Blank=1.pdf&Datum=2024-2&Gericht=bgh&Sort=1&anz=338&nr=137633&pos=23) | `juris.bundesgerichtshof.de` | ja | nein | nein | Aktuelle Einordnung des Merkmals ‚als Zeuge‘ in § 153 StGB als tatbezogenes persönliches Merkmal, auf das § 28 Abs. 1 StGB nicht anwendbar ist. |
| [Link](https://www.anwalt24.de/urteile/bgh/1955-10-24/gsst-1_55) | `www.anwalt24.de` | ja | nein | nein | Einheit von Aussage und unmittelbar anschließender Vereidigung sowie Abgrenzung zwischen § 153 und § 154 StGB. |
| [Link](https://www.gesetze-im-internet.de/stgb/BJNR001270871.html) | `www.gesetze-im-internet.de` | ja | nein | nein | Prüfung der aktuellen Fassungen der einschlägigen Straf- und Konkurrenzvorschriften, insbesondere §§ 22–24, 26, 28, 30, 31, 49, 52, 53, 123, 153–160, 242–244 StGB. |
| [Link](https://www.gesetze-im-internet.de/stpo/__59.html) | `www.gesetze-im-internet.de` | ja | nein | nein | Prüfung der Voraussetzungen und des Zeitpunkts der Zeugenvereidigung im Strafverfahren. |
| [Link](https://www.hrr-strafrecht.de/hrr/4/19/4-397-19.php) | `www.hrr-strafrecht.de` | ja | nein | nein | Unmittelbares Ansetzen beim Versuch des Wohnungseinbruchdiebstahls durch Beginn der qualifizierten Zugangshandlung. |

### Informative Such-Leakage-Flags

Diese Treffer sind Review-Hinweise. Sie kontaminieren oder verwerfen den Fall nicht.

- `task-identifier` (`zjs`): "22. Januar 2020" "seit dem Tod ihrer jeweils einzigen Bewohner" 244 -site:zjs-online.com
- `task-identifier` (`zjs`): "4 StR 265/22" "nach dem Tod des Bewohners" -site:zjs-online.com
- `task-identifier` (`zjs`): "5 StR 361/17" Wohnung Tod Bewohner § 244 -site:zjs-online.com
- `task-identifier` (`zjs`): "Eidesformel" "§ 153" "Rücktritt" Meineid Zeuge berichtigt -site:zjs-online.com
- `quoted-task-fragment` (`Eidesformel`): "Eidesformel" "§ 153" "Rücktritt" Meineid Zeuge berichtigt -site:zjs-online.com
- `task-identifier` (`zjs`): "Ich schw" versuchter Meineid Rücktritt Zeugenaussage -site:zjs-online.com
- `quoted-task-fragment` (`Ich schw`): "Ich schw" versuchter Meineid Rücktritt Zeugenaussage -site:zjs-online.com
- `task-identifier` (`zjs`): "Vernehmung als beendet" "§ 153" Vereidigung -site:zjs-online.com
- `task-identifier` (`zjs`): "Wohnungseigenschaft" "Tod ihres einzigen Bewohners" BGH -site:zjs-online.com
- `task-identifier` (`zjs`): "unmittelbaren Anschluß" Vereidigung § 153 § 154 Berichtigung -site:zjs-online.com
- `task-identifier` (`zjs`): "versuchten Meineid" "§ 153" Berichtigung Eidesformel -site:zjs-online.com
- `task-identifier` (`zjs`): BGH "als Zeuge" "besonderes persönliches Merkmal" 153 28 -site:zjs-online.com
- `quoted-task-fragment` (`als Zeuge`): BGH "als Zeuge" "besonderes persönliches Merkmal" 153 28 -site:zjs-online.com
- `task-identifier` (`zjs`): BGH 2024 "Formulierung als Zeuge" § 153 besonderes persönliches Merkmal § 28 -site:zjs-online.com
- `task-identifier` (`zjs`): BGH 244 Wohnung Tod Bewohner möbliert Erben Besitz Wohnungseinbruch -site:zjs-online.com
- `task-identifier` (`zjs`): BGH Aussage beendet Vereidigung Ich schwöre Versuch Meineid Rücktritt § 154 -site:zjs-online.com
- `task-identifier` (`zjs`): BGH Rücktritt Qualifikation Wohnungseinbruchdiebstahl Tür unverschlossen Werkzeug -site:zjs-online.com
- `task-identifier` (`zjs`): BGH Rücktritt Qualifikationsversuch vollendetes Grunddelikt -site:zjs-online.com
- `task-identifier` (`zjs`): BGH Wohnungseinbruchdiebstahl Bewohner verstorben Wohnungsqualität Aufgabe Wohnzweck -site:zjs-online.com
- `task-identifier` (`zjs`): BGH falsche uneidliche Aussage abgeschlossen Vernehmung Berichtigung vor Vereidigung Meineid Versuch -site:zjs-online.com
- `task-identifier` (`zjs`): BGH § 153 Vollendung Vernehmung beendet Vereidigung anschließend falsche uneidliche Aussage Meineid -site:zjs-online.com
- `task-identifier` (`zjs`): Bankkarte Tür geöffnet nicht verschlossen Wohnungseinbruchdiebstahl Versuch -site:zjs-online.com
- `task-identifier` (`zjs`): Kunststoffkarte Türschlitz Tür nicht abgeschlossen Versuch Wohnungseinbruchdiebstahl Rücktritt -site:zjs-online.com
- `task-identifier` (`zjs`): Plastikkarte unverschlossene Tür § 244 Versuch Wohnungseinbruchdiebstahl -site:zjs-online.com
- `task-identifier` (`zjs`): Rücktritt Versuch Qualifikation Grunddelikt vollendet § 244 Werkzeug aufgegeben -site:zjs-online.com
- `task-identifier` (`zjs`): Wohnungseinbruchdiebstahl Versuch Rücktritt Tür offen Grunddelikt vollendet -site:zjs-online.com
- `task-identifier` (`zjs`): Zeuge berichtigt Aussage während Eidesformel Strafbarkeit § 153 154 -site:zjs-online.com
- `task-identifier` (`zjs`): site:bundesgerichtshof.de "3 StR 526/19" -site:zjs-online.com
- `task-identifier` (`zjs`): site:bundesgerichtshof.de "4 StR 265/22" -site:zjs-online.com
- `task-identifier` (`zjs`): site:bundesgerichtshof.de Wohnung verstorbene Bewohnerin Wohnungseinbruchdiebstahl Tod Wohnungsqualität -site:zjs-online.com
- `task-identifier` (`zjs`): site:bundesgerichtshof.de uneidliche Falschaussage Berichtigung § 158 Zeugenvernehmung beendet Eid Versuch Meineid -site:zjs-online.com
- `task-identifier` (`zjs`): site:bundesgerichtshof.de § 153 § 28 "als Zeuge" -site:zjs-online.com
- `quoted-task-fragment` (`als Zeuge`): site:bundesgerichtshof.de § 153 § 28 "als Zeuge" -site:zjs-online.com
- `task-identifier` (`zjs`): site:gesetze-im-internet.de stgb § 153 § 154 § 158 falsche Aussage Berichtigung -site:zjs-online.com
- `task-identifier` (`zjs`): site:gesetze-im-internet.de stgb § 244 Wohnungseinbruchdiebstahl -site:zjs-online.com
- `task-identifier` (`zjs`): site:gesetze-im-internet.de/stpo/__59.html § 59 StPO Vereidigung Zeuge -site:zjs-online.com
- `task-identifier` (`zjs`): site:juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py "4 StR 397/19" -site:zjs-online.com
- `task-identifier` (`zjs`): site:juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py "6 StR 28/21" -site:zjs-online.com
- `task-identifier` (`zjs`): site:rechtsprechung-im-internet.de "3 StR 526/19" -site:zjs-online.com
- `task-identifier` (`zjs`): versuchte Qualifikation vollendetes Grunddelikt Rücktritt Qualifikationsversuch § 24 StGB -site:zjs-online.com
- `task-identifier` (`zjs`): § 153 StGB vollendet Abschluss Vernehmung anschließend Eid falsche Aussage -site:zjs-online.com

## Suchanfragen

- "22. Januar 2020" "seit dem Tod ihrer jeweils einzigen Bewohner" 244 -site:zjs-online.com
- "4 StR 265/22" "nach dem Tod des Bewohners" -site:zjs-online.com
- "5 StR 361/17" Wohnung Tod Bewohner § 244 -site:zjs-online.com
- "Eidesformel" "§ 153" "Rücktritt" Meineid Zeuge berichtigt -site:zjs-online.com
- "Ich schw" versuchter Meineid Rücktritt Zeugenaussage -site:zjs-online.com
- "Vernehmung als beendet" "§ 153" Vereidigung -site:zjs-online.com
- "Wohnungseigenschaft" "Tod ihres einzigen Bewohners" BGH -site:zjs-online.com
- "unmittelbaren Anschluß" Vereidigung § 153 § 154 Berichtigung -site:zjs-online.com
- "versuchten Meineid" "§ 153" Berichtigung Eidesformel -site:zjs-online.com
- BGH "als Zeuge" "besonderes persönliches Merkmal" 153 28 -site:zjs-online.com
- BGH 2024 "Formulierung als Zeuge" § 153 besonderes persönliches Merkmal § 28 -site:zjs-online.com
- BGH 244 Wohnung Tod Bewohner möbliert Erben Besitz Wohnungseinbruch -site:zjs-online.com
- BGH Aussage beendet Vereidigung Ich schwöre Versuch Meineid Rücktritt § 154 -site:zjs-online.com
- BGH Rücktritt Qualifikation Wohnungseinbruchdiebstahl Tür unverschlossen Werkzeug -site:zjs-online.com
- BGH Rücktritt Qualifikationsversuch vollendetes Grunddelikt -site:zjs-online.com
- BGH Wohnungseinbruchdiebstahl Bewohner verstorben Wohnungsqualität Aufgabe Wohnzweck -site:zjs-online.com
- BGH falsche uneidliche Aussage abgeschlossen Vernehmung Berichtigung vor Vereidigung Meineid Versuch -site:zjs-online.com
- BGH § 153 Vollendung Vernehmung beendet Vereidigung anschließend falsche uneidliche Aussage Meineid -site:zjs-online.com
- Bankkarte Tür geöffnet nicht verschlossen Wohnungseinbruchdiebstahl Versuch -site:zjs-online.com
- Kunststoffkarte Türschlitz Tür nicht abgeschlossen Versuch Wohnungseinbruchdiebstahl Rücktritt -site:zjs-online.com
- Plastikkarte unverschlossene Tür § 244 Versuch Wohnungseinbruchdiebstahl -site:zjs-online.com
- Rücktritt Versuch Qualifikation Grunddelikt vollendet § 244 Werkzeug aufgegeben -site:zjs-online.com
- Wohnungseinbruchdiebstahl Versuch Rücktritt Tür offen Grunddelikt vollendet -site:zjs-online.com
- Zeuge berichtigt Aussage während Eidesformel Strafbarkeit § 153 154 -site:zjs-online.com
- site:bundesgerichtshof.de "3 StR 526/19" -site:zjs-online.com
- site:bundesgerichtshof.de "4 StR 265/22" -site:zjs-online.com
- site:bundesgerichtshof.de Wohnung verstorbene Bewohnerin Wohnungseinbruchdiebstahl Tod Wohnungsqualität -site:zjs-online.com
- site:bundesgerichtshof.de uneidliche Falschaussage Berichtigung § 158 Zeugenvernehmung beendet Eid Versuch Meineid -site:zjs-online.com
- site:bundesgerichtshof.de § 153 § 28 "als Zeuge" -site:zjs-online.com
- site:gesetze-im-internet.de stgb § 153 § 154 § 158 falsche Aussage Berichtigung -site:zjs-online.com
- site:gesetze-im-internet.de stgb § 244 Wohnungseinbruchdiebstahl -site:zjs-online.com
- site:gesetze-im-internet.de/stpo/__59.html § 59 StPO Vereidigung Zeuge -site:zjs-online.com
- site:juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py "4 StR 397/19" -site:zjs-online.com
- site:juris.bundesgerichtshof.de/cgi-bin/rechtsprechung/document.py "6 StR 28/21" -site:zjs-online.com
- site:rechtsprechung-im-internet.de "3 StR 526/19" -site:zjs-online.com
- versuchte Qualifikation vollendetes Grunddelikt Rücktritt Qualifikationsversuch § 24 StGB -site:zjs-online.com
- § 153 StGB vollendet Abschluss Vernehmung anschließend Eid falsche Aussage -site:zjs-online.com

## Methodische Grenze

Used means the URL appears in the selected deliverable or in Codex's required .codex-used-sources.json sidecar. Open/Fetch means Codex additionally recorded an explicit page-open action or HTTP fetch command. Search-result URLs are not invented from snippets and are not counted unless one of those records exists.
