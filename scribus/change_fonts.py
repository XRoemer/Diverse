#!/usr/bin/python
# -*- coding: utf-8 -*-
# This version 27.3.2015

"""
Dieses Skript ersetzt Schriftarten und Schriftgr��en von mehreren Zeichenstilen gleichzeitig 
 
Installation:
Dieses Skript als change_fonts.py in den scribus Skriptordner kopieren
( in Win7 z.B. C:\Program Files\Scribus 1.4.5\share\scripts)
Das Skript muss als utf-8 codiert sein. (Beim Speichern mit dem Editor kann
man im Windows Editor neben dem Speicher-Button die Codierung ausw�hlen. -> UTF-8)

Variante 1
Skript in Scribus starten und Font und Schriftgr��e w�hlen. Den Button unter 
neue Schriftart klicken, um gew�nschte �nderungen f�r den entsprechenden Stil einzutragen.
Mit dem Startbutton werden die �nderungen �bernommen. Die �nderungen werden erst
nach dem Schlie�en des Skriptfensters sichtbar.

Variante 2:
In Zeile 178 bei scribus.redrawAll() das "#" entfernen.
In den allgemeinen Einstellungen unter Scripter das H�kchen bei "Erweiterungsscripte aktivieren" setzen.
Skript mit "Skript ausf�hren" starten und "Als Erweiterungsskript ausf�hren" aktivieren.
Wenn der Start Button im Skriptfenster bet�tigt wird, werden �nderungen sofort
sichtbar. Das Skript mu� nicht geschlossen und wieder ge�ffnet werden, allerdings
l�uft es instabiler und kann Scribus evt. zum Absturz bringen.
 
 
********** WARNUNG *************

Dieses Skript �berschreibt den vorhandenen Stil. �nderungen in der Laufweite
und dergleichen gehen verloren. Der Versuch, auch diese Einstellungen zu �bernehmen,
wurde unternommen (Zeilen 128ff und 226ff), funktioniert aber noch nicht. Wahrscheinlich liegt es 
an der Formatierung der Werte (String,Int,Float)

Stile mit Umlauten im Namen k�nnen nicht ge�ndert werden. Der Versuch f�hrt
zu neuen Stileintr�gen mit unicode Zeichen. Das Attribut 'name' kann in:
scribus.createCharStyle(name=stil ...) nicht mit unicode gesetzt werden.

 
"""



platform = sys.platform
         
def pydevBrk():  
    # adjust your path 
    if platform == 'linux':
        sys.path.append('/opt/eclipse/plugins/org.python.pydev_3.8.0.201409251235/pysrc')  
    else:
        sys.path.append(r'H:/Programme/eclipse/plugins/org.python.pydev_3.5.0.201405201709/pysrc')  
    from pydevd import settrace
    settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True) 
pd = pydevBrk 
#pd()

 
import scribus
from functools import partial
import StringIO


try:
    from PIL import Image as ImagePIL
    from PIL import ImageFont,ImageDraw
except ImportError:
    print "This script requires Python27 and PIL installed on your system."
    scribus.messageBox('Script failed',
               'This script requires Python27 and PIL installed on your system.',
               scribus.ICON_CRITICAL)
    sys.exit(1)

try:
    from Tkinter import *
except ImportError:
    print "This script requires Python27 and Tkinter installed on your system."
    scribus.messageBox('Script failed',
               'This script requires Python27 and Tkinter installed on your system.',
               scribus.ICON_CRITICAL)
    sys.exit(1)
 
 
 
class Exchange(Frame):
    """ GUI interface for exchanging a charstyle """
 
    def __init__(self, master=None):

        Frame.__init__(self, master)
        self.grid()
        self.master.geometry('950x730')
        self.master.title('Ersetze Stile')

        
        self.styles = self.get_styles()

        self.xfonts,self.xfonts_pfade = self.get_font_styles()
        
        self.btn_schnitte = []
        self.beispieltext = ''
        
        self.columnconfigure(5,weight = 1)
        
        
        Label(self, text='Stil',width ='20').grid(column=0, row=0,sticky=N,pady=10,padx=5)
        Label(self, text='Neue Schriftart',width ='20').grid(column=1, row=0,sticky=N,pady=10,padx=5)
        Label(self, text='pt',width ='3').grid(column=2, row=0,sticky=N,pady=10,padx=5)
        
        self.selektierter_schnitt = StringVar(master)  
        self.selektierter_schnitt.set('')
        
        
        self.neue_schrift = {}
        currRow = 1
        
        for f in range(len(self.styles)):
            
            var = StringVar(master)  
            var.set('KEINE AENDERUNG')
            self.neue_schrift.update({currRow:var})
            
            var = StringVar(master)  
            var.set('12')
            self.neue_schrift.update({str(currRow)+'fs':var})
            
            sty = self.styles[f] 
            
            stil_btn = Button(self, text=sty,width ='20')
            stil_btn.grid(column=0, row=currRow,sticky=N,pady=1,padx=5)
            
            
            n_stil_btn = Button(self, textvariable=self.neue_schrift[currRow],
                                width ='20',
                                command=partial(self.uebernehme_stil,currRow)
                                
                                )
            n_stil_btn.grid(column=1, row=currRow,sticky=N,pady=1,padx=5)
            
            f_size = Label(self, textvariable=self.neue_schrift[str(currRow)+'fs'],width ='3')
            f_size.grid(column=2, row=currRow,sticky=N,pady=1,padx=5)
            
            currRow += 1
        
        
        self.listbox = Listbox(self,height='45',width = '30')
        self.listbox.insert(END, u"KEINE AENDERUNG")
        
        for c in sorted(self.xfonts.keys()):
            self.listbox.insert(END, c) 
            
        self.listbox.grid(column=4, row=0,padx=5,rowspan=500)
        self.listbox.bind("<ButtonRelease-1>", self.setze_familie_und_schnitt)
        
        Label(self, text='Schriftgroesse',width ='10').grid(column=5, row=0,sticky=N,pady=15,padx=5)
        
        self.var_fs = StringVar(master)  
        self.var_fs.set('12')
        size = range(5,50)
        
        self.font_size = OptionMenu(self, self.var_fs, *size)
        self.font_size.grid(column=5, row=1)
        
                
        btn = Button(self, text = 'Start',width ='20',command=self.aendere_stile)
        btn.grid(column=1, row=400 ,pady=1,padx=5)

    
        
    def erstelle_beispieltext(self,text):
  
        W, H = (1500,100)
        
        if self.beispieltext != '':
            self.beispieltext.grid_forget()
        
        image = ImagePIL.new("RGBA", (W,H), (255,255,255))

        usr_font = ImageFont.truetype(self.xfonts_pfade[text.strip()], 18)
        msg = 'Beispieltext f�r Schrifttype:'
        msg2 = text
        draw = ImageDraw.Draw(image)

        draw.text( (5,0) , msg, (0,0,0), font=usr_font)
        w, h = draw.textsize(msg,font=usr_font)
        
        draw.text( (5,h) , msg2, (0,0,0), font=usr_font)
        w2, h2 = draw.textsize(msg2,font=usr_font)
        
        wmax = max(w,w2)

        image.size = (wmax+10,h+h2+5)
        
        # StringIO
        output = StringIO.StringIO()
        image.save(output, format="GIF")
        contents = output.getvalue()
        output.close()
        
        photo = PhotoImage(data=contents)
        self.beispieltext = Label(self, image=photo,width =W)
        self.beispieltext.grid(column=6, row=30)
        self.beispieltext.image = photo

   
 
    def alignImage(self):        
        self.master.destroy()
        
        
    def aendere_stile(self):
        
        for k in sorted(self.neue_schrift):
            if str(type(k)) == "<type 'int'>":
                
                neue_schriftart = self.neue_schrift[k].get()
                
                if neue_schriftart != 'KEINE AENDERUNG':
                    size = float(self.neue_schrift[str(k)+'fs'].get())
                    stil = self.styles[k-1]
                    
                    #self.style_info[stil].update({'font':neue_schriftart})
                    #self.style_info[stil]['fontsize'] = float(self.style_info[stil]['fontsize'])
                    #print(stil,neue_schriftart,size)
                    #self.test(**self.style_info[stil])
                    #scribus.createCharStyle(**self.style_info[stil])
                    
                    scribus.createCharStyle(name=stil,font=neue_schriftart,fontsize=size)
                    scribus.redrawAll()
                    
       
    def test(self,**args):
        print(args)
    
    
    def uebernehme_stil(self,ev):

        selektiert = self.selektierter_schnitt.get()
        if selektiert == '':
            return
        schnitt = selektiert.split(',')[0][2:-1]

        self.neue_schrift[ev].set(schnitt)
        self.neue_schrift[str(ev)+'fs'].set( self.var_fs.get())

        
    def setze_schnitt(self,ev):
        self.selektierter_schnitt.set(ev)
        self.erstelle_beispieltext(ev[0])
        
        
    def setze_familie_und_schnitt(self,*ev):

        for b in self.btn_schnitte:
            b[0].grid_forget()
            b[1].grid_forget()
                    
        
        selek = self.listbox.get(self.listbox.curselection())
        
        if selek == 'KEINE AENDERUNG':
            self.selektierter_schnitt.set("['KEINE AENDERUNG'")
        
        else:
            
            schriftarten = self.xfonts[selek]
            
            currRow = 5 + 50
            for s in schriftarten:
                radio_btn = Radiobutton(self,
                                        value=currRow,
                                        command=partial(self.setze_schnitt,s),
                                        )
                
                radio_btn.grid(column=5, row=currRow,sticky=E)
                
                label = Label(self,
                            text = s[1],
                            padx = 2
                            )
                
                label.grid(column=6, row=currRow,sticky=W)
                
                self.btn_schnitte.append((radio_btn,label))
                currRow += 1
                
            self.btn_schnitte[0][0].select()
            self.selektierter_schnitt.set(schriftarten[0])

            self.erstelle_beispieltext(schriftarten[0][0])
            

    def get_styles(self):
        
        from xml.etree import ElementTree as et
        
        path = scribus.getDocName()
        xml_tree = et.parse(path)
        root = xml_tree.getroot()
        
        elem = root.findall('.//CHARSTYLE')  
        
        styles =[]
        self.style_info = {}
        
        for e in elem:
            styles.append(e.attrib['CNAME'])

            stylefx = (           
                    ('fontsize','FONTSIZE'),
                    ("features",'FEATURES'),
                    ("fillcolor",'FCOLOR'),
                    ('fillshade','FSHADE'),
                    ("strokecolor",'SCOLOR'),
                    ('strokeshade','SSHADE'),
                    ('baselineoffset','BASEO'), 
                    ('shadowxoffset','TXTSHX'),
                    ('shadowyoffset','TXTSHY'),
                    ('outlinewidth','TXTOUT'),
                    ('underlineoffset','TXTULP'),
                    ('underlinewidth','TXTULW'),
                    ('strikethruoffset','TXTSTP'),
                    ('strikethruwidth','TXTSTW'),
                    ('scaleh','SCALEH'),
                    ('scalev','SCALEV'), 
                    ('tracking','KERN'),
                    ("language",'LANGUAGE')
                    )
            
            d_dic = {}
            d_dic.update({'name':e.attrib['CNAME']})
            
            for fx in stylefx:
                if fx[1] in e.attrib:
                    try:
                        val = int (e.attrib[fx[1]])
                    except:
                        try:
                            val = float(e.attrib[fx[1]])
                        except:
                            val = e.attrib[fx[1]]
                    
                    d_dic.update({fx[0]:val})
                
            self.style_info.update({e.attrib['CNAME']:d_dic})
                
        return styles
        
    
    def get_font_styles(self):
        
        xfonts = scribus.getXFontNames()
        
        fam = {}
        fonts_pfade = {}
        for f in xfonts:
            
            schnitt =  f[2].split('-')
            if len(schnitt) == 1:
                schnitt = 'Regular'
            else:
                schnitt = schnitt[1]
            
            if f[1] not in fam:
                fam.update( { f[1] : [ (f[0],schnitt) ] } )
            else:
                fam[f[1]].append( (f[0],schnitt) )

            fonts_pfade.update( {f[0].strip(): f[-1]} )
        return fam,fonts_pfade
        
        
 
def main():
    
    try:
        root = Tk()
        app = Exchange(root)
        root.mainloop()
    finally:
        if scribus.haveDoc():
            scribus.redrawAll()
 
if __name__ == '__main__':
    main()