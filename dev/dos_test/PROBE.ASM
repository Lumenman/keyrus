.8086
.model tiny
.code
org 100h
start:
 mov ax,4100h
 int 16h
 cmp ax,0aaaah
 jne fail
 cmp cx,'KR'
 jne fail
 mov es,dx
 cmp byte ptr ds:[80h],0
 je api
 mov bx,es:[53h]
 and bx,7fffh
 cmp word ptr es:[bx],9dh
 jne fail
 cmp word ptr es:[bx+2],9dh
 jne fail
api:
 mov ax,4190h
 int 16h
 mov ax,4101h
 int 16h
 and bl,3
 jne fail
 mov ax,414ch
 int 16h
 mov ax,4101h
 int 16h
 and bl,3
 cmp bl,1
 jne fail
 mov dx,offset ok
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
fail:
 mov dx,offset bad
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
ok db 'PASS',13,10,'$'
bad db 'FAIL',13,10,'$'
end start
