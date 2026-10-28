import sys
p=sys.argv[1]; msg=sys.argv[2]
files=[]
for l in open(p).read().split('\n'):
    if l.startswith('commit:') or not l.strip(): continue
    if l not in files: files.append(l)
open(p,'w').write("commit: "+msg+"\n"+"\n".join(files)+"\n")
