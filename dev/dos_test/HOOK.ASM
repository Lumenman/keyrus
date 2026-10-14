.8086
.model tiny
.code
org 100h
start:
 jmp setup
handler:
 db 0eah
oldoff dw 0
oldseg dw 0
magic dw 0f3a3h
setup:
 cmp byte ptr ds:[80h],0
 jne remove
 mov ax,3516h
 int 21h
 mov oldoff,bx
 mov oldseg,es
 mov dx,offset handler
 mov ax,2516h
 int 21h
 mov dx,offset finish
 int 27h
remove:
 mov ax,3516h
 int 21h
 cmp word ptr es:[bx+5],0f3a3h
 jne fail
 push ds
 lds dx,es:[bx+1]
 mov ax,2516h
 int 21h
 pop ds
 mov ah,49h
 int 21h
 mov ax,4c00h
 int 21h
fail:
 mov ax,4c01h
 int 21h
finish:
end start
