# OpenCode Trace

2. `read` via `read` paths: `/work/documents/sachverhalt.md` lines 1-3
5. `read` via `bash` paths: `/work/documents/sachverhalt.md`
   command: `cat /work/documents/sachverhalt.md`
8. `write` via `write` paths: `/work/fallloesung.md`
11. `shell` via `bash` paths: `/work/fallloesung.md`
   command: `wc -l /work/fallloesung.md && head -5 /work/fallloesung.md && echo "---" && tail -5 /work/fallloesung.md`
14. `list` via `bash` paths: `/work/fallloesung.md`
   command: `ls -la /work/fallloesung.md`
17. `read` via `read` paths: `/work/fallloesung.md` lines 1-10
