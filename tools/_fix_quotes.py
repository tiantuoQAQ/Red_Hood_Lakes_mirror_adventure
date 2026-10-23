# 修复被 PowerShell here-string 吞掉的属性引号（sprite.* 相关）
import io, re

p = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam\index.html'
t = io.open(p, encoding='utf-8').read()

before = len(re.findall(r'data-(?:cfg|out)=sprite\.', t))
t = re.sub(r'(data-(?:cfg|out))=(sprite\.[A-Za-z]+)', r'\1="\2"', t)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('fixed unquoted sprite attrs:', before)
