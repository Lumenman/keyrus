.8086
.model tiny
.code
org 100h
start:
 mov ax,4100h
 int 16h
 mov bp,dx
 mov ax,dx
 call hex
 mov es,bp
 mov ax,es:[59h]
 call hex
 mov ax,es:[57h]
 call hex
 mov ax,es:[63h]
 call hex
 mov bx,es:[53h]
 mov ax,es:[bx+10]
 call hex
 xor ax,ax
 mov es,ax
 mov si,8*4
 call vec
 mov si,16h*4
 call vec
 mov si,10h*4
 call vec
 mov si,9*4
 call vec
 int 20h
vec:
 mov ax,es:[si]
 call hex
 mov ax,es:[si+2]
 call hex
 ret
hex:
 push ax
 push bx
 push cx
 push dx
 mov bx,ax
 mov cx,4
again:
 push cx
 mov cl,4
 rol bx,cl
 pop cx
 mov dl,bl
 and dl,15
 add dl,'0'
 cmp dl,'9'
 jbe digit
 add dl,7
digit:
 mov ah,2
 int 21h
 loop again
 mov dl,' '
 int 21h
 pop dx
 pop cx
 pop bx
 pop ax
 ret
end start
