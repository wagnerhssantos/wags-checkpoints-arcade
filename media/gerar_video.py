# UAI MODO TURBO — Fase Final (pixel art 90s) — gerador de vídeo
import math, random, subprocess
from PIL import Image, ImageDraw

W, H, FPS = 384, 216, 24
SCALE = 5
random.seed(7)

import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE = os.path.join(ROOT, "data", "scoreboard.json")
OUT = os.path.join(ROOT, "media", "uai-modo-turbo-fase-final.mp4")
FALLBACK = [
 ("GIULIA",240,"OURO"),("ANGELICA",232,"PRATA"),("GABRIELLE",197,"PRATA"),
 ("GUILHERME",192,"PRATA"),("ANGELA",185,"PRATA"),("ANDRESA",185,"PRATA"),
 ("RANDAL",180,"PRATA"),("THIAGO",179,"PRATA"),("LUCAS",175,"PRATA"),
 ("CAREN",165,"PRATA"),("MARCELO",165,"PRATA"),("KISSILA",127,"BRONZE"),
 ("LUCRECIA",115,"BRONZE"),("MAYCON",95,"BRONZE")]
DATA_DATE = "25/09"
try:  # ranking vem do placar oficial publicado no repo (não recalcula nada)
    sb = json.load(open(SCORE, encoding="utf-8"))
    res = sorted(sb["results"], key=lambda r: -r["total"])
    AGENTS = [(r["agent"].split(".")[0].upper(), r["total"], r["level"]) for r in res]
    y, m, d_ = sb["dataAsOf"].split("-"); DATA_DATE = f"{d_}/{m}"
except Exception as e:
    print("scoreboard.json indisponível, usando ranking de 25/09:", e); AGENTS = FALLBACK
if len(sys.argv) > 1: OUT = sys.argv[1]
LONG = {"GIULIA","ANGELICA","GABRIELLE","ANGELA","ANDRESA","CAREN","KISSILA","LUCRECIA"}

# ---------- fonte 3x5 ----------
G = {
'A':"010101111101101",'B':"110101110101110",'C':"011100100100011",'D':"110101101101110",
'E':"111100110100111",'F':"111100110100100",'G':"011100101101011",'H':"101101111101101",
'I':"111010010010111",'J':"001001001101010",'K':"101101110101101",'L':"100100100100111",
'M':"101111111101101",'N':"110101101101101",'O':"010101101101010",'P':"110101110100100",
'Q':"010101101110011",'R':"110101110101101",'S':"011100010001110",'T':"111010010010010",
'U':"101101101101111",'V':"101101101101010",'W':"101101111111101",'X':"101101010101101",
'Y':"101101010010010",'Z':"111001010100111",
'0':"111101101101111",'1':"010110010010111",'2':"110001010100111",'3':"110001010001110",
'4':"101101111001001",'5':"111100110001110",'6':"011100111101111",'7':"111001010010010",
'8':"111101111101111",'9':"111101111001110",
' ':"000000000000000",'!':"010010010000010",'.':"000000000000010",':':"000010000010000",
'/':"001001010100100",'-':"000000111000000",'?':"110001010000010",',':"000000000010100",
'º':"010101010000111",'·':"000000010000000",'>':"100010001010100",
}
ACC = {'À':('A','grave'),'Á':('A','acute'),'Ã':('A','til'),'É':('E','acute'),'Ê':('E','circ'),
       'Ó':('O','acute'),'Ç':('C','ced'),'Í':('I','acute')}
def text(d, s, x, y, col, sc=1, shadow=None):
    cx = x
    for ch in s:
        base, acc = (ACC[ch] if ch in ACC else (ch, None))
        g = G.get(base, G['?'])
        for layer in ([shadow, col] if shadow else [col]):
            off = sc if layer is shadow and shadow else 0
            for i,b in enumerate(g):
                if b=='1':
                    px, py = cx+(i%3)*sc+off, y+(i//3)*sc+off
                    d.rectangle([px,py,px+sc-1,py+sc-1], fill=layer)
            if acc:
                pts = {'grave':[(0,-2),(1,-1)],'acute':[(2,-2),(1,-1)],'til':[(0,-1),(1,-2),(2,-1)],
                       'circ':[(0,-1),(1,-2),(2,-1)],'ced':[(1,5),(1,6)]}[acc]
                for (a,b2) in pts:
                    px, py = cx+a*sc+off, y+b2*sc+off
                    d.rectangle([px,py,px+sc-1,py+sc-1], fill=layer)
        cx += 4*sc
def tw(s, sc=1): return len(s)*4*sc - sc
def ctext(d, s, y, col, sc=1, shadow=None, cx=W//2):
    text(d, s, cx - tw(s,sc)//2, y, col, sc, shadow)

# ---------- paleta ----------
PUR=(123,44,191); PUR_L=(170,96,230); PUR_D=(72,20,120); CAPE=(90,24,150); CAPE_D=(58,12,100)
YEL=(255,214,0); BOOT=(40,16,70); WHT=(255,255,255); BLK=(12,6,24)
GOLD=(255,200,40); SILV=(210,215,230); BRNZ=(210,130,60)
SKINS=[(255,214,170),(233,180,130),(198,134,90),(150,96,60),(110,70,45)]
HAIRS=[(40,24,16),(90,50,20),(20,20,24),(160,90,40),(230,190,90),(120,30,30),(60,40,30)]

BODY = [
 "...HHHH...",
 "..HHHHHH..",
 "..HSSSSS..",
 "..HMWMMW..",
 "...SSSSS..",
 ".CPPLPPP..",
 "CCPYYPPPS.",
 "CCPYYPPPS.",
 "CCPPPPPP..",
 "CCYYYYYY..",
 "C.PPPPPP..",
]
LEGS = [
 ["..PP..PP..","..PP...PP.",".BB.....BB"],
 ["...PPPP...","...PPPP...","...BBBB..."],
 ["...PP.PP..","..PP..PP..","..BB..BB.."],
 ["...PPPP...","...PPPP...","...BBBB..."],
]
STAND = ["...PP.PP..","...PP.PP..","..BBB.BBB."]
def sprite(skin, hair, long_, frame, pose="walk"):
    im = Image.new("RGBA",(10,14),(0,0,0,0)); px = im.load()
    rows = BODY + (LEGS[frame%4] if pose=="walk" else STAND)
    cmap = {'H':hair,'S':skin,'M':PUR_D,'W':WHT,'P':PUR,'L':PUR_L,'C':CAPE,'Y':YEL,'B':BOOT}
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c in cmap: px[x,y] = cmap[c]+(255,)
    if long_:
        for y in (3,4,5): px[2,y] = hair+(255,)
        px[1,4]=hair+(255,)
    # capa esvoaçante
    if pose=="walk" and frame%2==0:
        px[0,11]=CAPE_D+(255,); px[0,10]=CAPE+(255,)
    if pose=="cheer":  # braço pra cima
        px[8,6]=(0,0,0,0); px[8,7]=(0,0,0,0); px[8,4]=skin+(255,); px[8,5]=PUR+(255,); px[8,3]=skin+(255,)
    return im

HEROES=[]
for i,(n,p,l) in enumerate(AGENTS):
    skin = SKINS[(i*3)%len(SKINS)]; hair = HAIRS[(i*5+1)%len(HAIRS)]
    fr = {k:sprite(skin,hair,n in LONG,k) for k in range(4)}
    fr['stand']=sprite(skin,hair,n in LONG,0,"stand")
    fr['cheer']=sprite(skin,hair,n in LONG,0,"cheer")
    HEROES.append(fr)
def big(im,s): return im.resize((im.width*s, im.height*s), Image.NEAREST)

# ---------- cenário ----------
STARS=[(random.randrange(W),random.randrange(0,100),random.random()) for _ in range(60)]
def sky(d, t):
    bands=[(20,8,48),(34,12,72),(52,18,98),(78,30,128),(110,48,150),(150,70,160)]
    bh=22
    for i,c in enumerate(bands):
        d.rectangle([0,i*bh,W,(i+1)*bh],fill=c)
        if i+1<len(bands):  # dither
            for x in range(0,W,2):
                d.point((x+(i%2),(i+1)*bh-1),fill=bands[i+1])
    d.rectangle([0,len(bands)*bh,W,H],fill=bands[-1])
    for (x,y,ph) in STARS:
        if math.sin(t*4+ph*10)>-0.3: d.point((x,y),fill=(255,240,200))
    # lua
    d.ellipse([300,18,322,40],fill=(255,236,180)); d.ellipse([306,16,328,38],fill=bands[0] if False else (255,236,180))
def mountains(d, cam, par, base, col, amp, per, seed):
    off = cam*par
    pts=[(0,H)]
    for x in range(0,W+8,4):
        wx = x+off
        y = base - amp*abs(math.sin(wx/per+seed)) - amp*0.4*abs(math.sin(wx/(per*0.37)+seed*2))
        pts.append((x,int(y)))
    pts.append((W,H)); d.polygon(pts,fill=col)
def city(d, cam):
    off = int(cam*0.5)
    rnd = random.Random(3)
    bx=-(off%600)
    for rep in range(3):
        x=bx+rep*600; rnd.seed(3)
        while x < bx+rep*600+600:
            w=rnd.randint(18,34); h=rnd.randint(30,70)
            if x+w>0 and x<W:
                d.rectangle([x,168-h,x+w,168],fill=(58,22,96))
                for wy in range(168-h+5,164,7):
                    for wx in range(x+4,x+w-3,6):
                        if rnd.random()<0.55: d.rectangle([wx,wy,wx+2,wy+3],fill=(255,210,90))
                        else: d.rectangle([wx,wy,wx+2,wy+3],fill=(40,14,70))
            else:
                for _ in range(40): rnd.random()
            x+=w+rnd.randint(2,8)
def ground(d, cam):
    d.rectangle([0,176,W,H],fill=(120,60,30))
    d.rectangle([0,176,W,179],fill=(70,200,90)); d.rectangle([0,180,W,181],fill=(40,140,60))
    off=int(cam)%16
    for y in range(184,H,8):
        sh = 8 if (y//8)%2 else 0
        for x in range(-off-16+sh, W+16, 16):
            d.rectangle([x,y,x+15,y+7],outline=(80,36,16))
def hud(d, t, stage="STAGE 09/26"):
    d.rectangle([0,0,W,12],fill=BLK)
    text(d,"UAI MODO TURBO",4,4,YEL)
    ctext(d,stage,4,WHT)
    s="TIME "+str(max(0,99-int(t*3))).zfill(2)
    text(d,s,W-tw(s)-4,4,WHT)

def coinblocks(d, cam, t):
    for k in range(12):
        wx=260+k*230; x=int(wx-cam)
        if -20<x<W+20:
            y=110
            d.rectangle([x,y,x+11,y+11],fill=(230,150,20),outline=BLK)
            text(d,"?",x+4,y+3,WHT)
            # moeda girando
            ph=abs(math.sin(t*5+k)); cw=max(1,int(4*ph))
            d.ellipse([x+6-cw,y-14,x+6+cw,y-4],fill=YEL,outline=(180,120,0))

def castle(d, x):
    x=int(x)
    base=176
    d.rectangle([x,base-90,x+110,base],fill=(64,24,104))
    for k in range(0,111,14): d.rectangle([x+k,base-98,x+k+8,base-90],fill=(64,24,104))
    d.rectangle([x-18,base-120,x+10,base],fill=(84,34,134))
    d.rectangle([x+100,base-120,x+128,base],fill=(84,34,134))
    for tx in (x-18,x+100):
        for k in range(0,29,10): d.rectangle([tx+k,base-128,tx+k+6,base-120],fill=(84,34,134))
    # tijolos
    for yy in range(base-88,base,8):
        for xx in range(x+((yy//8)%2)*7,x+110,14): d.rectangle([xx,yy,xx+13,yy+7],outline=(50,16,84))
    # bandeira
    d.line([x+114,base-150,x+114,base-128],fill=WHT)
    d.polygon([(x+115,base-150),(x+132,base-145),(x+115,base-140)],fill=YEL)
    # porta
    d.rectangle([x+38,base-52,x+72,base],fill=BLK)
    d.ellipse([x+38,base-68,x+72,base-36],fill=BLK)
    # placa
    d.rectangle([x+14,base-84,x+96,base-72],fill=YEL,outline=BLK)
    ctext(d,"FASE FINAL",base-81,BLK,cx=x+55)
    return x+38, x+72

def label(d, name, x, y, col):
    w=tw(name); d.rectangle([x-w//2-2,y-2,x+w//2+2,y+6],fill=BLK)
    text(d,name,x-w//2,y,col)

def name_col(i): return [GOLD,SILV,BRNZ][i] if i<3 else WHT

frames=[]
def T(sec): return int(sec*FPS)
TOTAL=T(27)
out = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24",
    "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-vf",f"scale={W*SCALE}:{H*SCALE}:flags=neighbor",
    "-c:v","libx264","-preset","slow","-crf","16","-tune","animation","-pix_fmt","yuv420p",
    "-movflags","+faststart",OUT],stdin=subprocess.PIPE)
def emit(im): out.stdin.write(im.convert("RGB").tobytes())

HS=2  # heróis em 2x
SP=26
CONF=[(random.randrange(W),random.randrange(-H,0),random.choice([GOLD,PUR_L,(90,220,255),(255,90,160),WHT]),random.uniform(20,50)) for _ in range(120)]

for f in range(TOTAL):
    t=f/FPS
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    # ---------------- CENA 1: título ----------------
    if t<3.5:
        sky(d,t)
        mountains(d,t*20,0.2,150,(40,14,70),30,40,1)
        ctext(d,"UAI MODO TURBO",46,YEL,sc=4,shadow=PUR_D)
        ctext(d,"TIME WAGS · SETEMBRO 2026",82,WHT,sc=2,shadow=BLK)
        # herói grande
        sp=big(HEROES[0][int(t*6)%4],5); im.paste(sp,(W//2-25,108),sp)
        if int(t*2.5)%2==0: ctext(d,"PRESS START",190,WHT,sc=2,shadow=BLK)
        text(d,"CSI NUBANK 2026",W-tw("CSI NUBANK 2026")-4,H-8,(180,160,210))
        if t>3.1:  # flash
            a=int(255*(t-3.1)/0.4); ov=Image.new("RGB",(W,H),WHT); im=Image.blend(im,ov,min(1,a/255))
        emit(im); continue
    # ---------------- CENA 2 e 3: caminhada ----------------
    if t<16.5:
        tl=t-3.5
        WALK=38  # px/s
        CASTLE_WX=600
        stop_cam = CASTLE_WX-250
        cam=min(max(0,(tl-2)*WALK*1.6), stop_cam)
        sky(d,t); mountains(d,cam,0.15,140,(46,16,80),28,50,2)
        city(d,cam); mountains(d,cam,0.35,172,(30,90,70),10,20,5)
        ground(d,cam); coinblocks(d,cam,t)
        gx0,gx1=castle(d,CASTLE_WX-cam)
        door=(gx0+gx1)/2
        hud(d,t)
        # posição dos heróis (screen)
        lead = min(40+tl*WALK*1.6, 200)  # líder entra e para em ~250 enquanto câmera anda
        arrived = cam>=stop_cam
        t_arr = (stop_cam/(WALK*1.6))+2 if True else 0
        after = max(0, tl - t_arr)
        order=list(range(len(AGENTS)))[::-1]
        for i in order:
            lane = i%2
            baseY = 176-14*HS + (0 if lane==0 else 3)
            x = lead - i*SP + (0 if lane==0 else 4)
            pose = int(t*8+i)%4
            spr=None; yoff=0
            if i<3:
                # top3 continuam até a porta
                if after>0:
                    x = min(x + after*WALK, door-10 + (i-1)*0)
                    if x>=door-10: 
                        x=door-10
                        # entra (some) em sequência
                        vis_t = after - (door-10-(lead - i*SP))/WALK
                        if vis_t>0.4: continue
                    spr=HEROES[i][pose]
                else: spr=HEROES[i][pose]
            else:
                if after>0:
                    x = lead - i*SP + (0 if lane==0 else 4)
                    x = x  # parados
                    ph=(after*3+i*0.37)%1
                    yoff = -int(abs(math.sin((after*4+i)*1.0))*10)
                    spr=HEROES[i]['cheer']
                else: spr=HEROES[i][pose]
            sp=big(spr,HS); im.paste(sp,(int(x)-10,int(baseY+yoff)),sp)
            ly = int(baseY+yoff) - 9 - (i%3)*8
            label(d,AGENTS[i][0],int(x),ly,name_col(i))
        # recobre a porta por cima pra "entrar"
        if 0<tl<3.5:
            ctext(d,"STAGE 09 · RUMO À FASE FINAL!",40,WHT,sc=2,shadow=BLK)
        if after>0.3:
            if int(t*3)%2==0: ctext(d,"SÓ O TOP 3 ENTRA NA FASE FINAL!",40,YEL,sc=2,shadow=BLK)
        if t>16.0:
            a=(t-16.0)/0.5; im=Image.blend(im,Image.new("RGB",(W,H),BLK),min(1,a))
        emit(im); continue
    # ---------------- CENA 4: pódio ----------------
    tp=t-16.5
    # salão do chefe
    d.rectangle([0,0,W,H],fill=(26,8,50))
    for k in range(0,W,24): d.rectangle([k,0,k+11,H],fill=(32,10,60))
    # holofotes
    for (cx,ph) in ((W//2,0),(W//2-90,1.3),(W//2+90,2.1)):
        sw=int(18+6*math.sin(tp*2+ph))
        d.polygon([(cx-4,12),(cx+4,12),(cx+sw+26,176),(cx-sw-26,176)],fill=(48,22,84))
    d.rectangle([0,176,W,H],fill=(60,20,100)); d.rectangle([0,176,W,178],fill=YEL)
    hud(d,t,"FASE FINAL")
    ctext(d,"PARABÉNS, HERÓIS!",22,YEL,sc=3,shadow=PUR_D)
    pods=[(1,W//2-78,40,SILV,"2"),(0,W//2,62,GOLD,"1"),(2,W//2+78,26,BRNZ,"3")]
    for (i,cx,hgt,col,num) in pods:
        top=176-hgt
        d.rectangle([cx-30,top,cx+30,176],fill=col,outline=BLK)
        d.rectangle([cx-30,top,cx+30,top+3],fill=tuple(min(255,c+40) for c in col))
        ctext(d,num+"º",top+8,BLK,sc=3,cx=cx)
        # herói cai do céu
        delay={0:1.6,1:0.6,2:1.1}[i]
        land_y=top-14*3
        tt=tp-delay
        if tt<0: continue
        y = min(land_y, -50 + tt*tt*420)
        if y>=land_y:
            j=tp-delay-math.sqrt((land_y+50)/420)
            y = land_y - int(abs(math.sin(j*5+i))*12) if j>0.3 else land_y
            spr=HEROES[i]['cheer'] if int(j*5+i)%2==0 else HEROES[i]['stand']
            n,pts,lvl=AGENTS[i]
            label(d,n,cx,land_y-26,col)
            ctext(d,f"{pts} PTS · {lvl}",land_y-15,WHT,cx=cx)
        else: spr=HEROES[i]['stand']
        sp=big(spr,3); im.paste(sp,(cx-15,int(y)),sp)
        if i==0 and y>=land_y-20:  # coroa
            cy=int(y)-6
            d.polygon([(cx-6,cy+5),(cx-6,cy),(cx-3,cy+3),(cx,cy-1),(cx+3,cy+3),(cx+6,cy),(cx+6,cy+5)],fill=GOLD,outline=BLK)
    if tp>2.2:
        for (x,y0,c,v) in CONF:
            y=(y0+(tp-2.2)*v*2)%(H+20)-10
            xx=x+int(4*math.sin(tp*3+x))
            d.rectangle([xx,int(y),xx+1,int(y)+2],fill=c)
    ctext(d,f"PLACAR PARCIAL {DATA_DATE} · RESULTADO OFICIAL 29/09",196,(210,190,240))
    if tp>7.8 and int(t*2.5)%2==0: ctext(d,"CONTINUE? MÉTRICAS FECHAM 30/09",206,YEL)
    if t>26.3:
        im=Image.blend(im,Image.new("RGB",(W,H),BLK),min(1,(t-26.3)/0.7))
    emit(im)
out.stdin.close(); out.wait()
print("ok")
