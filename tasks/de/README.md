# Deutsche Fälle

Die deutschen Fälle sind fachlich und nicht nach ihrer Quellensammlung geordnet:

```text
tasks/de/
├── oeffentliches-recht/
│   ├── europarecht/
│   ├── staatshaftungsrecht/
│   ├── staatsrecht/
│   │   └── grundrechte/
│   ├── referendariat/
│   ├── verwaltungsrecht/
│   │   └── asylrecht/
│   └── voelkerrecht/
├── strafrecht/
│   ├── kriminologie-und-nebengebiete/
│   ├── materielles-strafrecht/
│   ├── strafprozessrecht/
│   └── wirtschaftsstrafrecht/
├── zivilrecht/
│   ├── arbeitsrecht/
│   ├── familien-und-erbrecht/
│   ├── handels-und-gesellschaftsrecht/
│   ├── sachenrecht/
│   └── schuldrecht/
└── provenance/
    ├── lab-de-urhg-60d/
    └── zjs/
```

Die Herkunft eines Falls bleibt unabhängig von seinem Ablageort nachvollziehbar:

- Lizenz- und Quellenangaben stehen im jeweiligen `task.json`.
- Der Importnachweis der ZJS-Fälle liegt in
  [`provenance/zjs/source-map.json`](provenance/zjs/source-map.json).
- Die zugehörige Zitationsdatei liegt in
  [`provenance/zjs/CITATION.cff`](provenance/zjs/CITATION.cff).
- Die Herkunft der 22 Fälle aus `LAB-DE-UrhG-60d` ist unter
  [`provenance/lab-de-urhg-60d/`](provenance/lab-de-urhg-60d/) dokumentiert.
