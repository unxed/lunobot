import re,sys
W="/tmp/lunobot-1/work/tv3-cont2-1028"
log,name,dest=sys.argv[1:4]
out=[];on=False
for l in open(log,encoding='utf-8',errors='replace').read().split('\n'):
    if '----- BEGIN src/%s.inc -----'%name in l and 'echo' not in l: on=True; continue
    if '----- END src/%s.inc -----'%name in l and 'echo' not in l: on=False; continue
    if on and l.startswith('linux\t'):
        out.append(l.split('Z ',1)[1] if 'Z ' in l else '')
print(name,len(out))
if out: open(dest,'w',encoding='utf-8',newline='\n').write("\n".join(out)+"\n")
