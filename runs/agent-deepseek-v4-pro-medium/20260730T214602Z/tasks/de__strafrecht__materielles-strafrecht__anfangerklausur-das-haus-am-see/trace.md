# OpenCode Trace

2. `read` via `read` paths: `/work/documents/sachverhalt.md` lines 1-3
5. `read` via `read` paths: `/work/documents/sachverhalt.md` lines 1-3
8. `read` via `bash` paths: `/work/documents/sachverhalt.md`
   command: `cat /work/documents/sachverhalt.md`
11. `list` via `glob` pattern `**/*.md`
14. `write` via `write` paths: `/work/fallloesung.md`
17. `shell` via `bash` paths: `/work/fallloesung.md`
   command: `wc -l /work/fallloesung.md && wc -c /work/fallloesung.md`
20. `list` via `bash` paths: `/work/fallloesung.md`
   command: `ls -la /work/fallloesung.md`
